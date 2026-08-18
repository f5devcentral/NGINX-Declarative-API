#!/usr/bin/python3

"""
NGINX Declarative API
"""
from contextlib import asynccontextmanager
import json
import logging
import threading
import time

import schedule
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response, JSONResponse
import warnings

# NGINX Declarative API modules
import NcgConfig
from NcgRedis import NcgRedis
from AppLogger import AppLogger, get_logger

import V5_5_CreateConfig
import V5_5_NginxConfigDeclaration
import v5_5.Asynchronous

import V5_6_CreateConfig
import V5_6_NginxConfigDeclaration
import v5_6.Asynchronous

import V5_7_CreateConfig
import V5_7_NginxConfigDeclaration
import v5_7.Asynchronous

# Suppress the Pydantic serialization unexpected value warnings
warnings.filterwarnings(
    "ignore",
    message="Pydantic serializer warnings:",
    category=UserWarning
)

cfg = NcgConfig.NcgConfig(configFile="../etc/config.yaml")
is_debug = cfg.config.get('log', {}).get('level') == 'DEBUG'
redis = NcgRedis(host=cfg.config['redis']['host'], port=cfg.config['redis']['port'])


def parse_bool(val) -> bool:
    """Safely converts boolean or string representations ('True', 'False', True, False) to bool."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes", "on")
    return bool(val)


def configure_logging():
    """
    Initializes/reconfigures the AppLogger singleton from config.yaml and routes Uvicorn/FastAPI internal loggers.
    """
    log_cfg = cfg.config.get('log', {})

    level = log_cfg.get('level', 'INFO')
    stdout = parse_bool(log_cfg.get('stdout', True))
    stderr = parse_bool(log_cfg.get('stderr', False))

    file_enabled = parse_bool(log_cfg.get('file', False))
    file_path = log_cfg.get('filename') if file_enabled else None

    syslog_enabled = parse_bool(log_cfg.get('syslog', False))
    syslog_host = log_cfg.get('syslog_host') if syslog_enabled else None
    syslog_port = int(log_cfg.get('syslog_port', 514))

    # Reconfigure singleton instance explicitly
    singleton = AppLogger()
    singleton.configure(
        level=level,
        fmt="[%(asctime)s] [%(levelname)s] [%(filename)s:%(funcName)s:%(lineno)d] %(message)s",
        stdout=stdout,
        stderr=stderr,
        file_path=file_path,
        syslog_host=syslog_host,
        syslog_port=syslog_port,
    )

    # Route Uvicorn and FastAPI internal loggers to use the singleton handlers
    singleton_handlers = singleton.logger.handlers
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        uv_logger = logging.getLogger(logger_name)
        uv_logger.handlers = singleton_handlers
        uv_logger.propagate = False

    return singleton


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event: configure logging
    configure_logging()
    logger = get_logger()
    logger.info("FastAPI application startup complete.")
    yield
    # Shutdown event
    logger.info("FastAPI application shutting down.")


app = FastAPI(
    title=cfg.config['main']['banner'],
    version=cfg.config['main']['version'],
    contact={"name": "GitHub", "url": cfg.config['main']['url']},
    debug=is_debug,
    lifespan=lifespan
)


# HTTP Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = get_logger()
    start_time = time.perf_counter()

    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path
    query = request.url.query

    # Read and restore request body stream for Pydantic parsing
    body_bytes = await request.body()

    async def receive():
        return {"type": "http.request", "body": body_bytes}

    request._receive = receive

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"--> Incoming Request: {method} {path}" + (f"?{query}" if query else "") + f" from {client_ip}")
        logger.debug(f"--> Headers: {dict(request.headers)}")
        if body_bytes:
            logger.debug(f"--> Body Payload:\n{body_bytes.decode('utf-8', errors='ignore')}")

    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        log_msg = f"HTTP {method} {path} -> Status {response.status_code} ({duration_ms:.2f}ms)"

        if response.status_code >= 500:
            logger.error(log_msg, stacklevel=3)
        elif response.status_code >= 400:
            logger.warning(log_msg, stacklevel=3)
        else:
            logger.info(log_msg)

        return response
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.exception(f"HTTP {method} {path} -> Unhandled Exception: {exc} ({duration_ms:.2f}ms)")
        raise exc


#
# GitOps autosync scheduler
#
def runGitOpsScheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


#
# Asynchronous declaration worker
#
def runAsynchronousWorker():
    logger = get_logger()
    while True:
        time.sleep(cfg.config['nms']['asynchronous_publish_waittime'])
        item = redis.asyncQueue.get()
        logger.info(
            f"Processing asynchronous declaration: API [{item['apiVersion']}] method [{item['method']}] configUid [{item['configUid']}] submissionUid [{item['submissionUid']}]")
        declaration = item['declaration']

        if item['apiVersion'] == 'v5.5':
            response = V5_5_CreateConfig.patch_config(declaration=declaration, configUid=item['configUid'],
                                                      apiversion=item['apiVersion'])
        elif item['apiVersion'] == 'v5.6':
            response = V5_6_CreateConfig.patch_config(declaration=declaration, configUid=item['configUid'],
                                                      apiversion=item['apiVersion'])
        elif item['apiVersion'] == 'v5.7':
            response = V5_7_CreateConfig.patch_config(declaration=declaration, configUid=item['configUid'],
                                                      apiversion=item['apiVersion'])

        NcgRedis.redis.set(f"ncg.async.submission.{item['submissionUid']}", response.body.decode("utf-8"))

        redis.asyncQueue.task_done()


# Submit declaration using v5.5 API
@app.post("/v5.5/config", status_code=200, response_class=PlainTextResponse)
def post_config_v5_5(d: V5_5_NginxConfigDeclaration.ConfigDeclaration, response: Response):
    output = V5_5_CreateConfig.createconfig(declaration=d, apiversion='v5.5')

    headers = output['message']['headers'] if 'headers' in output['message'] else {'Content-Type': 'application/json'}

    if 'message' in output:
        if 'message' in output['message']:
            response = output['message']['message']
        else:
            response = output['message']
    else:
        response = output

    return JSONResponse(content=response, status_code=output['status_code'], headers=headers)


# Submit declaration using v5.6 API
@app.post("/v5.6/config", status_code=200, response_class=PlainTextResponse)
def post_config_v5_6(d: V5_6_NginxConfigDeclaration.ConfigDeclaration, response: Response):
    output = V5_6_CreateConfig.createconfig(declaration=d, apiversion='v5.6')

    headers = output['message']['headers'] if 'headers' in output['message'] else {'Content-Type': 'application/json'}

    if 'message' in output:
        if 'message' in output['message']:
            response = output['message']['message']
        else:
            response = output['message']
    else:
        response = output

    return JSONResponse(content=response, status_code=output['status_code'], headers=headers)


# Submit declaration using v5.7 API
@app.post("/v5.7/config", status_code=200, response_class=PlainTextResponse)
def post_config_v5_7(d: V5_7_NginxConfigDeclaration.ConfigDeclaration, response: Response):
    output = V5_7_CreateConfig.createconfig(declaration=d, apiversion='v5.7')

    headers = output['message']['headers'] if 'headers' in output['message'] else {'Content-Type': 'application/json'}

    if 'message' in output:
        if 'message' in output['message']:
            response = output['message']['message']
        else:
            response = output['message']
    else:
        response = output

    return JSONResponse(content=response, status_code=output['status_code'], headers=headers)


# Modify declaration using v5.5 API
@app.patch("/v5.5/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def patch_config_v5_5(d: V5_5_NginxConfigDeclaration.ConfigDeclaration, response: Response, configuid: str):
    retcode, response = v5_5.Asynchronous.checkIfAsynch(declaration=d, method='PATCH', apiVersion='v5.5',
                                                        configUid=configuid)

    if retcode is not None:
        # Request was asynchronous and it has been submitted to the FIFO queue
        return JSONResponse(content=response, status_code=retcode, headers={'Content-Type': 'application/json'})

    return V5_5_CreateConfig.patch_config(declaration=d, configUid=configuid, apiversion='v5.5')


# Modify declaration using v5.6 API
@app.patch("/v5.6/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def patch_config_v5_6(d: V5_6_NginxConfigDeclaration.ConfigDeclaration, response: Response, configuid: str):
    retcode, response = v5_6.Asynchronous.checkIfAsynch(declaration=d, method='PATCH', apiVersion='v5.6',
                                                        configUid=configuid)

    if retcode is not None:
        # Request was asynchronous and it has been submitted to the FIFO queue
        return JSONResponse(content=response, status_code=retcode, headers={'Content-Type': 'application/json'})

    return V5_6_CreateConfig.patch_config(declaration=d, configUid=configuid, apiversion='v5.6')


# Modify declaration using v5.7 API
@app.patch("/v5.7/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def patch_config_v5_7(d: V5_7_NginxConfigDeclaration.ConfigDeclaration, response: Response, configuid: str):
    retcode, response = v5_7.Asynchronous.checkIfAsynch(declaration=d, method='PATCH', apiVersion='v5.7',
                                                        configUid=configuid)

    if retcode is not None:
        # Request was asynchronous and it has been submitted to the FIFO queue
        return JSONResponse(content=response, status_code=retcode, headers={'Content-Type': 'application/json'})

    return V5_7_CreateConfig.patch_config(declaration=d, configUid=configuid, apiversion='v5.7')


# Get declaration - v5.5 API
@app.get("/v5.5/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def get_config_declaration_v5_5(configuid: str):
    status_code, content = V5_5_CreateConfig.get_declaration(configUid=configuid)

    if status_code == 404:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'declaration {configuid} not found'}},
            headers={'Content-Type': 'application/json'}
        )

    return JSONResponse(
        status_code=200,
        content=content,
        headers={'Content-Type': 'application/json'}
    )


# Get declaration - v5.6 API
@app.get("/v5.6/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def get_config_declaration_v5_6(configuid: str):
    status_code, content = V5_6_CreateConfig.get_declaration(configUid=configuid)

    if status_code == 404:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'declaration {configuid} not found'}},
            headers={'Content-Type': 'application/json'}
        )

    return JSONResponse(
        status_code=200,
        content=content,
        headers={'Content-Type': 'application/json'}
    )


# Get declaration - v5.7 API
@app.get("/v5.7/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def get_config_declaration_v5_7(configuid: str):
    status_code, content = V5_7_CreateConfig.get_declaration(configUid=configuid)

    if status_code == 404:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'declaration {configuid} not found'}},
            headers={'Content-Type': 'application/json'}
        )

    return JSONResponse(
        status_code=200,
        content=content,
        headers={'Content-Type': 'application/json'}
    )


# Get declaration status
@app.get("/v5.5/config/{configuid}/status", status_code=200, response_class=PlainTextResponse)
@app.get("/v5.6/config/{configuid}/status", status_code=200, response_class=PlainTextResponse)
@app.get("/v5.7/config/{configuid}/status", status_code=200, response_class=PlainTextResponse)
def get_config_status(configuid: str):
    global redis
    status = redis.redis.get('ncg.status.' + configuid)

    if status is None:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'declaration {configuid} not found'}},
            headers={'Content-Type': 'application/json'}
        )
    else:
        return JSONResponse(
            status_code=200,
            content=json.loads(status),
            headers={'Content-Type': 'application/json'}
        )


# Get asynchronous submission status
@app.get("/v5.5/config/{configuid}/submission/{submissionuid}", status_code=200, response_class=PlainTextResponse)
@app.get("/v5.6/config/{configuid}/submission/{submissionuid}", status_code=200, response_class=PlainTextResponse)
@app.get("/v5.7/config/{configuid}/submission/{submissionuid}", status_code=200, response_class=PlainTextResponse)
def get_submission_status(configuid: str, submissionuid: str):
    logger = get_logger()
    status = redis.redis.get('ncg.async.submission.' + submissionuid)

    if status is None:
        return JSONResponse(
            status_code=404,
            content={'code': 404,
                     'details': {'message': f'submission {submissionuid} for declaration {configuid} not found'}},
            headers={'Content-Type': 'application/json'}
        )
    else:
        jsonStatus = json.loads(status)

        if 'details' in jsonStatus and 'message' in jsonStatus['details']:
            # Remove the redis entry for ncg.async.submission if configuration publish has been run from the FIFO queue
            # If the submission is still pending in the queue, it is not removed
            logger.info(f"Removing status for submission id {submissionuid} for config {configuid}")
            redis.redis.delete('ncg.async.submission.' + submissionuid)

        return JSONResponse(
            status_code=200,
            content=json.loads(status),
            headers={'Content-Type': 'application/json'}
        )


# Delete declaration
@app.delete("/v5.5/config/{configuid}", status_code=200, response_class=PlainTextResponse)
@app.delete("/v5.6/config/{configuid}", status_code=200, response_class=PlainTextResponse)
@app.delete("/v5.7/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def delete_config(configuid: str = ""):
    logger = get_logger()
    if configuid not in redis.declarationsList:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'declaration {configuid} not found'}},
            headers={'Content-Type': 'application/json'}
        )

    job = redis.declarationsList[configuid]

    redis.declarationsList.pop(configuid, None)
    redis.redis.delete('ncg.declaration.' + configuid)
    redis.redis.delete('ncg.declarationrendered.' + configuid)
    redis.redis.delete('ncg.apiversion.' + configuid)
    redis.redis.delete('ncg.status.' + configuid)
    redis.redis.delete('ncg.basestagedconfig.' + configuid)

    if job != "static":
        # Kills autosync GitOps config thread
        logger.info(f"Terminating autosync for declaration [{configuid}]")
        schedule.cancel_job(job)
    else:
        logger.info(f"Deleting declaration configuid [{configuid}]")

    return JSONResponse(
        status_code=200,
        content={'code': 200, 'details': {'message': f'declaration {configuid} deleted'}},
        headers={'Content-Type': 'application/json'}
    )


# Get JSON schema for the v5.5 ConfigDeclaration - used by the Web UI editor for IntelliSense
@app.get("/v5.5/schema", status_code=200)
def get_schema_v5_5():
    schema = V5_5_NginxConfigDeclaration.ConfigDeclaration.model_json_schema()
    return JSONResponse(content=schema, headers={'Content-Type': 'application/json'})


# Get JSON schema for the v5.6 ConfigDeclaration - used by the Web UI editor for IntelliSense
@app.get("/v5.6/schema", status_code=200)
def get_schema_v5_6():
    schema = V5_6_NginxConfigDeclaration.ConfigDeclaration.model_json_schema()
    return JSONResponse(content=schema, headers={'Content-Type': 'application/json'})


# Get JSON schema for the v5.6 ConfigDeclaration - used by the Web UI editor for IntelliSense
@app.get("/v5.7/schema", status_code=200)
def get_schema_v5_7():
    schema = V5_7_NginxConfigDeclaration.ConfigDeclaration.model_json_schema()
    return JSONResponse(content=schema, headers={'Content-Type': 'application/json'})


# NGINX Declarative API main
def main():
    configure_logging()
    logger = get_logger()
    logger.info(f"{cfg.config['main']['banner']} {cfg.config['main']['version']}")

    logger.info("Starting GitOps scheduler")
    threading.Thread(target=runGitOpsScheduler, daemon=True).start()

    logger.info("Starting Asynchronous declarations scheduler")
    threading.Thread(target=runAsynchronousWorker, daemon=True).start()

    apiServerHost = cfg.config['apiserver']['host']
    apiServerPort = cfg.config['apiserver']['port']

    logger.info(f"Starting API server on {apiServerHost}:{apiServerPort}")
    uvicorn.run("main:app", host=apiServerHost, port=apiServerPort, log_config=None)


if __name__ == '__main__':
    main()