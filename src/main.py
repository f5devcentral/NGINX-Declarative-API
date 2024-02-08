#!/usr/bin/python3

"""
NGINX Declarative API
"""
import json
import threading
import time

import schedule
import uvicorn
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response, JSONResponse

# NGINX Declarative API modules
import NcgConfig
import NcgRedis

import V4_0_CreateConfig
import V4_0_NginxConfigDeclaration

import V4_1_CreateConfig
import V4_1_NginxConfigDeclaration

import V4_2_CreateConfig
import V4_2_NginxConfigDeclaration


cfg = NcgConfig.NcgConfig(configFile="../etc/config.toml")
redis = NcgRedis.NcgRedis(host=cfg.config['redis']['host'], port=cfg.config['redis']['port'])

app = FastAPI(
    title=cfg.config['main']['banner'],
    version=cfg.config['main']['version'],
    contact={"name": "GitHub", "url": cfg.config['main']['url']}
)

# GitOps autosync scheduler
def runScheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


# Submit declaration using v4.0 API
@app.post("/v4.0/config", status_code=200, response_class=PlainTextResponse)
def post_config_v4_0(d: V4_0_NginxConfigDeclaration.ConfigDeclaration, response: Response):
    output = V4_0_CreateConfig.createconfig(declaration=d, apiversion='v4.0')

    if type(output) in [Response, str]:
        # ConfigMap or plaintext response
        return output

    headers = output['message']['headers'] if 'headers' in output['message'] else {'Content-Type': 'application/json'}

    if 'message' in output:
        if 'message' in output['message']:
            response = output['message']['message']
        else:
            response = output['message']
    else:
        response = output

    return JSONResponse(content=response, status_code=output['status_code'], headers=headers)


# Submit declaration using v4.1 API
@app.post("/v4.1/config", status_code=200, response_class=PlainTextResponse)
def post_config_v4_1(d: V4_1_NginxConfigDeclaration.ConfigDeclaration, response: Response):
    output = V4_1_CreateConfig.createconfig(declaration=d, apiversion='v4.1')

    if type(output) in [Response, str]:
        # ConfigMap or plaintext response
        return output

    headers = output['message']['headers'] if 'headers' in output['message'] else {'Content-Type': 'application/json'}

    if 'message' in output:
        if 'message' in output['message']:
            response = output['message']['message']
        else:
            response = output['message']
    else:
        response = output

    return JSONResponse(content=response, status_code=output['status_code'], headers=headers)


# Submit declaration using v4.2 API
@app.post("/v4.2/config", status_code=200, response_class=PlainTextResponse)
def post_config_v4_2(d: V4_2_NginxConfigDeclaration.ConfigDeclaration, response: Response):
    output = V4_2_CreateConfig.createconfig(declaration=d, apiversion='v4.2')

    if type(output) in [Response, str]:
        # ConfigMap or plaintext response
        return output

    headers = output['message']['headers'] if 'headers' in output['message'] else {'Content-Type': 'application/json'}

    if 'message' in output:
        if 'message' in output['message']:
            response = output['message']['message']
        else:
            response = output['message']
    else:
        response = output

    return JSONResponse(content=response, status_code=output['status_code'], headers=headers)


# Modify declaration using v4.0 API
@app.patch("/v4.0/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def patch_config_v4_0(d: V4_0_NginxConfigDeclaration.ConfigDeclaration, response: Response, configuid: str):
    return V4_0_CreateConfig.patch_config(declaration=d, configUid=configuid, apiversion='v4.0')


# Modify declaration using v4.1 API
@app.patch("/v4.1/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def patch_config_v4_1(d: V4_1_NginxConfigDeclaration.ConfigDeclaration, response: Response, configuid: str):
    return V4_1_CreateConfig.patch_config(declaration=d, configUid=configuid, apiversion='v4.1')


# Modify declaration using v4.2 API
@app.patch("/v4.2/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def patch_config_v4_2(d: V4_2_NginxConfigDeclaration.ConfigDeclaration, response: Response, configuid: str):
    return V4_2_CreateConfig.patch_config(declaration=d, configUid=configuid, apiversion='v4.2')


# Get declaration - v4.0 API
@app.get("/v4.0/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def get_config_declaration_v4_0(configuid: str):
    status_code, content = V4_0_CreateConfig.get_declaration(configUid=configuid)

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


# Get declaration - v4.1 API
@app.get("/v4.1/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def get_config_declaration_v4_1(configuid: str):
    status_code, content = V4_1_CreateConfig.get_declaration(configUid=configuid)

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



# Get declaration - v4.2 API
@app.get("/v4.2/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def get_config_declaration_v4_2(configuid: str):
    status_code, content = V4_2_CreateConfig.get_declaration(configUid=configuid)

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
@app.get("/v4.0/config/{configuid}/status", status_code=200, response_class=PlainTextResponse)
@app.get("/v4.1/config/{configuid}/status", status_code=200, response_class=PlainTextResponse)
@app.get("/v4.2/config/{configuid}/status", status_code=200, response_class=PlainTextResponse)
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


# Delete declaration
@app.delete("/v4.0/config/{configuid}", status_code=200, response_class=PlainTextResponse)
@app.delete("/v4.1/config/{configuid}", status_code=200, response_class=PlainTextResponse)
@app.delete("/v4.2/config/{configuid}", status_code=200, response_class=PlainTextResponse)
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


if __name__ == '__main__':
    print(f"{cfg.config['main']['banner']} {cfg.config['main']['version']}")

    print("Starting GitOps scheduler")
    schedulerThread = threading.Thread(target=runScheduler)
    schedulerThread.start()

    apiServerHost = cfg.config['apiserver']['host']
    apiServerPort = cfg.config['apiserver']['port']

    print(f"Starting API server on {apiServerHost}:{apiServerPort}")
    uvicorn.run("main:app", host=apiServerHost, port=apiServerPort)