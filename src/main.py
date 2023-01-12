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

from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse, Response, JSONResponse

# pydantic models
import V0_NginxConfigDeclaration
import V1_NginxConfigDeclaration

# NGINX Declarative API modules
import NcgConfig
import NcgRedis

import V0_CreateConfig
import V1_CreateConfig

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


# Get a Gitops declaration
@app.get("/v1/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def get_config_declaration(configuid: str):
    cfg = redis.redis.get('ncg.declaration.' + configuid)

    if cfg is None:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'configuration {configuid} not found'}},
            headers={'Content-Type': 'application/json'}
        )
    else:
        obj = pickle.loads(cfg)

        return JSONResponse(
            status_code=200,
            content=obj.dict(),
            headers={'Content-Type': 'application/json'}
        )


# Get a Gitops declaration status
@app.get("/v1/config/{configuid}/status", status_code=200, response_class=PlainTextResponse)
def get_config_status(configuid: str):
    status = redis.redis.get('ncg.status.' + configuid)

    if status is None:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'configuration {configuid} not found'}},
            headers={'Content-Type': 'application/json'}
        )
    else:
        return JSONResponse(
            status_code=200,
            content=json.loads(status),
            headers={'Content-Type': 'application/json'}
        )

# Delete a Gitops declaration
@app.delete("/v1/config/{configuid}", status_code=200, response_class=PlainTextResponse)
def delete_config(configuid: str):

    if configuid not in redis.autoSyncJobs:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'configuration {configuid} not found'}},
            headers={'Content-Type': 'application/json'}
        )
    else:
        print(f"Terminating autosync for configuid [{configuid}]")

        job = redis.autoSyncJobs[configuid]
        redis.autoSyncJobs.pop(configuid,None)
        redis.redis.delete('ncg.declaration.'+configuid)
        redis.redis.delete('ncg.apiversion.'+configuid)
        redis.redis.delete('ncg.status.'+configuid)
        redis.redis.delete('ncg.basestagedconfig.'+configuid)

        schedule.cancel_job(job)

        return JSONResponse(
            status_code=200,
            content={'code': 200, 'details': {'message': f'configuration {configuid} deleted'}},
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
