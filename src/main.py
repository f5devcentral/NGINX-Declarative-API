#!/usr/bin/python3

"""
NGINX Declarative API
"""
import json
import threading
import time
import queue

import schedule
import uvicorn
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response, JSONResponse

# NGINX Declarative API modules
import NcgConfig
from NcgRedis import NcgRedis

import V5_4_CreateConfig
import V5_4_NginxConfigDeclaration
import v5_4.Asynchronous

import V5_5_CreateConfig
import V5_5_NginxConfigDeclaration
import v5_5.Asynchronous

cfg = NcgConfig.NcgConfig(configFile="../etc/config.toml")
redis = NcgRedis(host=cfg.config['redis']['host'], port=cfg.config['redis']['port'])

app = FastAPI(
    title=cfg.config['main']['banner'],
    version=cfg.config['main']['version'],
    contact={"name": "GitHub", "url": cfg.config['main']['url']}
)

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
    while True:
        time.sleep(cfg.config['nms']['asynchronous_publish_waittime'])
        item = redis.asyncQueue.get()
        print(f"Processing asynchronous declaration: API [{item['apiVersion']}] method [{item['method']}] configUid [{item['configUid']}] submissionUid [{item['submissionUid']}]")
        declaration = item['declaration']

        if item['apiVersion'] == 'v5.4':
            response = V5_4_CreateConfig.patch_config(declaration = declaration, configUid = item['configUid'], apiversion = item['apiVersion'])
        elif item['apiVersion'] == 'v5.5':
            response = V5_5_CreateConfig.patch_config(declaration = declaration, configUid = item['configUid'], apiversion = item['apiVersion'])

        NcgRedis.redis.set(f"ncg.async.submission.{item['submissionUid']}", response.body.decode("utf-8"))

        redis.asyncQueue.task_done()

# Submit declaration using v5.4 API
@app.post("/v5.4/config", status_code=200, response_class=PlainTextResponse)
def post_config_v5_4(d: V5_4_NginxConfigDeclaration.ConfigDeclaration, response: Response):
    output = V5_4_CreateConfig.createconfig(declaration=d, apiversion='v5.4')

    #if type(output) in [Response, str]:
    #    # ConfigMap or plaintext response
    #    return output

    headers = output['message']['headers'] if 'headers' in output['message'] else {'Content-Type': 'application/json'}

    if 'message' in output:
        if 'message' in output['message']:
            response = output['message']['message']
        else:
            response = output['message']
    else:
        response = output

    return JSONResponse(content=response, status_code=output['status_code'], headers=headers)


# Submit declaration using v5.5 API
@app.post("/v5.5/config", status_code=200, response_class=PlainTextResponse)
def post_config_v5_5(d: V5_5_NginxConfigDeclaration.ConfigDeclaration, response: Response):
    output = V5_5_CreateConfig.createconfig(declaration=d, apiversion='v5.5')

    #if type(output) in [Response, str]:
    #    # ConfigMap or plaintext response
    #    return output

    headers = output['message']['headers'] if 'headers' in output['message'] else {'Content-Type': 'application/json'}

    if 'message' in output:
        if 'message' in output['message']:
            response = output['message']['message']
        else:
            response = output['message']
    else:
        response = output

    return JSONResponse(content=response, status_code=output['status_code'], headers=headers)


# Modify declaration using v5.4 API
@app.patch("/v5.4/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def patch_config_v5_4(d: V5_4_NginxConfigDeclaration.ConfigDeclaration, response: Response, configuid: str):
    retcode, response = v5_4.Asynchronous.checkIfAsynch(declaration = d, method = 'PATCH', apiVersion = 'v5.4', configUid = configuid)

    if retcode is not None:
        # Request was asynchronous and it has been submitted to the FIFO queue
        return JSONResponse(content=response, status_code = retcode, headers = {'Content-Type': 'application/json'})

    return V5_4_CreateConfig.patch_config(declaration=d, configUid=configuid, apiversion='v5.4')


# Modify declaration using v5.5 API
@app.patch("/v5.5/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def patch_config_v5_5(d: V5_5_NginxConfigDeclaration.ConfigDeclaration, response: Response, configuid: str):
    retcode, response = v5_5.Asynchronous.checkIfAsynch(declaration = d, method = 'PATCH', apiVersion = 'v5.5', configUid = configuid)

    if retcode is not None:
        # Request was asynchronous and it has been submitted to the FIFO queue
        return JSONResponse(content=response, status_code = retcode, headers = {'Content-Type': 'application/json'})

    return V5_5_CreateConfig.patch_config(declaration=d, configUid=configuid, apiversion='v5.5')


# Get declaration - v5.4 API
@app.get("/v5.4/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def get_config_declaration_v5_4(configuid: str):
    status_code, content = V5_4_CreateConfig.get_declaration(configUid=configuid)

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


# Get declaration status
@app.get("/v5.4/config/{configuid}/status", status_code=200, response_class=PlainTextResponse)
@app.get("/v5.5/config/{configuid}/status", status_code=200, response_class=PlainTextResponse)
def get_config_status(configuid: str):
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


# Get asynchronous submission status - v5.4 API
@app.get("/v5.4/config/{configuid}/submission/{submissionuid}", status_code=200, response_class=PlainTextResponse)
def get_submission_status(configuid: str, submissionuid: str):
    status = redis.redis.get('ncg.async.submission.' + submissionuid)

    if status is None:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'submission {submissionuid} for declaration {configuid} not found'}},
            headers={'Content-Type': 'application/json'}
        )
    else:
        jsonStatus = json.loads(status)

        if 'details' in jsonStatus and 'message' in jsonStatus['details']:
            # Remove the redis entry for ncg.async.submission if configuration publish has been run from the FIFO queue
            # If the submission is still pending in the queue, it is not removed
            print(f"Removing status for submission id {submissionuid} for config {configuid}")
            redis.redis.delete('ncg.async.submission.' + submissionuid)

        return JSONResponse(
            status_code=200,
            content=json.loads(status),
            headers={'Content-Type': 'application/json'}
        )


# Get asynchronous submission status - v5.5 API
@app.get("/v5.5/config/{configuid}/submission/{submissionuid}", status_code=200, response_class=PlainTextResponse)
def get_submission_status(configuid: str, submissionuid: str):
    status = redis.redis.get('ncg.async.submission.' + submissionuid)

    if status is None:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'submission {submissionuid} for declaration {configuid} not found'}},
            headers={'Content-Type': 'application/json'}
        )
    else:
        jsonStatus = json.loads(status)

        if 'details' in jsonStatus and 'message' in jsonStatus['details']:
            # Remove the redis entry for ncg.async.submission if configuration publish has been run from the FIFO queue
            # If the submission is still pending in the queue, it is not removed
            print(f"Removing status for submission id {submissionuid} for config {configuid}")
            redis.redis.delete('ncg.async.submission.' + submissionuid)

        return JSONResponse(
            status_code=200,
            content=json.loads(status),
            headers={'Content-Type': 'application/json'}
        )


# Delete declaration
@app.delete("/v5.4/config/{configuid}", status_code=200, response_class=PlainTextResponse)
@app.delete("/v5.5/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def delete_config(configuid: str = ""):
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
        print(f"Terminating autosync for declaration [{configuid}]")
        schedule.cancel_job(job)
    else:
        print(f"Deleting declaration configuid [{configuid}]")

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


if __name__ == '__main__':
    print(f"{cfg.config['main']['banner']} {cfg.config['main']['version']}")

    print("Starting GitOps scheduler")
    threading.Thread(target=runGitOpsScheduler).start()

    print("Starting Asynchronous declarations scheduler")
    threading.Thread(target=runAsynchronousWorker, daemon=True).start()

    apiServerHost = cfg.config['apiserver']['host']
    apiServerPort = cfg.config['apiserver']['port']

    print(f"Starting API server on {apiServerHost}:{apiServerPort}")
    uvicorn.run("main:app", host=apiServerHost, port=apiServerPort)