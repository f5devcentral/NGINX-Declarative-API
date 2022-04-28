#!/usr/bin/python3

"""
NGINX Configuration Generator
"""
import uvicorn

from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse

# pydantic models
from NginxConfigDeclaration import *

# NGINX Configuration Generator modules
import NcgConfig
import CreateConfig

cfg = NcgConfig.NcgConfig("../etc/config.toml")

app = FastAPI(
    title=cfg.config['main']['banner'],
    version=cfg.config['main']['version'],
    contact={"name":" ","url":cfg.config['main']['url']}
)


@app.post("/v0/config", status_code=200, response_class=PlainTextResponse)
def post_config(d: ConfigDeclaration, response: Response):
    return CreateConfig.createconfig(declaration=d,type=d.dict()['output']['type'])


if __name__ == '__main__':
    print(f"{cfg.config['main']['banner']} {cfg.config['main']['version']}")

    apiServerHost = cfg.config['apiserver']['host']
    apiServerPort = cfg.config['apiserver']['port']

    print(f"Starting API server on {apiServerHost}:{apiServerPort}")
    uvicorn.run("main:app", host=apiServerHost, port=apiServerPort)
