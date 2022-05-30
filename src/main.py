#!/usr/bin/python3

"""
NGINX Configuration Generator
"""
import uvicorn

from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse

# pydantic models
import V0_NginxConfigDeclaration
import V1_NginxConfigDeclaration

# NGINX Configuration Generator modules
import NcgConfig
import V0_CreateConfig
import V1_CreateConfig

cfg = NcgConfig.NcgConfig("../etc/config.toml")

app = FastAPI(
    title=cfg.config['main']['banner'],
    version=cfg.config['main']['version'],
    contact={"name": " ", "url": cfg.config['main']['url']}
)


@app.post("/v0/config", status_code=200, response_class=PlainTextResponse)
def post_config(d: V0_NginxConfigDeclaration.ConfigDeclaration, response: Response):
    return V0_CreateConfig.createconfig(declaration=d, apiversion='v0')


@app.post("/v1/config", status_code=200, response_class=PlainTextResponse)
def post_config(d: V1_NginxConfigDeclaration.ConfigDeclaration, response: Response):
    return V1_CreateConfig.createconfig(declaration=d, apiversion='v1')


if __name__ == '__main__':
    print(f"{cfg.config['main']['banner']} {cfg.config['main']['version']}")

    apiServerHost = cfg.config['apiserver']['host']
    apiServerPort = cfg.config['apiserver']['port']

    print(f"Starting API server on {apiServerHost}:{apiServerPort}")
    uvicorn.run("main:app", host=apiServerHost, port=apiServerPort)
