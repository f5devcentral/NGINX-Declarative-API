#!/usr/bin/python3

"""
NGINX Declarative API
"""
import uvicorn
import threading
import time
import schedule
import json
import pickle

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response, JSONResponse

# pydantic models

# NGINX Declarative API modules
import NcgConfig
import NcgRedis

from src import V0_CreateConfig, V0_NginxConfigDeclaration, V1_CreateConfig, V1_NginxConfigDeclaration, \
    V2_NginxConfigDeclaration, V2_CreateConfig

cfg = NcgConfig.NcgConfig(configFile="../etc/config.toml")
redis = NcgRedis.NcgRedis(host=cfg.config['redis']['host'], port=cfg.config['redis']['port'])

app = FastAPI(
    title=cfg.config['main']['banner'],
    version=cfg.config['main']['version'],
    contact={"name": "GitHub", "url": cfg.config['main']['url']}
)


def runScheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


# Submit a declaration using v0 API
@app.post("/v0/config", status_code=200, response_class=PlainTextResponse)
def post_config_v0_deprecated(d: V0_NginxConfigDeclaration.ConfigDeclaration, response: Response):
    return V0_CreateConfig.createconfig(declaration=d, apiversion='v0')


# Submit a declaration using v1 API
@app.post("/v1/config", status_code=200, response_class=PlainTextResponse)
def post_config_v1(d: V1_NginxConfigDeclaration.ConfigDeclaration, response: Response):
    return V1_CreateConfig.createconfig(declaration=d, apiversion='v1')


# Get declaration - v1 API
@app.get("/v1/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def get_config_declaration(configuid: str):
    return V1_CreateConfig.get_config(configUid=configuid)


# Submit declaration using v2 API
@app.post("/v2/config", status_code=200, response_class=PlainTextResponse)
def post_config_v2(d: V2_NginxConfigDeclaration.ConfigDeclaration, response: Response):
    output = V2_CreateConfig.createconfig(declaration=d, apiversion='v2')

    headers = output['headers'] if 'headers' in output else {'Content-Type': 'application/json'}

    if type(output) is str:
        return output

    return JSONResponse(content=output['message']['message'], status_code=output['status_code'], headers=headers)


# Modify eclaration using v2 API
@app.patch("/v2/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def patch_config_v2(d: V2_NginxConfigDeclaration.ConfigDeclaration, response: Response, configuid: str):
    return V2_CreateConfig.patch_config(declaration=d, configUid=configuid, apiversion='v2')


# Get declaration - v2 API
@app.get("/v2/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def get_config_declaration(configuid: str):
    status_code, content = V2_CreateConfig.get_declaration(configUid=configuid)

    if status_code == 404:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'declaration {configUid} not found'}},
            headers={'Content-Type': 'application/json'}
        )

    return JSONResponse(
        status_code=200,
        content=content,
        headers={'Content-Type': 'application/json'}
    )


# Get declaration status - v1 & v2 API
@app.get("/v1/config/{configuid}/status", status_code=200, response_class=PlainTextResponse)
@app.get("/v2/config/{configuid}/status", status_code=200, response_class=PlainTextResponse)
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

# Delete declaration - v1 & v2 API
@app.delete("/v1/config/{configuid}", status_code=200, response_class=PlainTextResponse)
@app.delete("/v2/config/{configuid}", status_code=200, response_class=PlainTextResponse)
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
