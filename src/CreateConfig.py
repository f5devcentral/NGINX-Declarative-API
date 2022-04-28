"""
Configuration creation based on jinja2 templates
"""

import base64

from jinja2 import Environment, FileSystemLoader
from fastapi.responses import Response,JSONResponse

# pydantic models
from NginxConfigDeclaration import *

# NGINX Configuration Generator modules
from NcgConfig import NcgConfig

def createconfig(declaration: ConfigDeclaration,type: str):
    # Building NGINX configuration for declaration.json()
    d = declaration.dict()

    j2_env = Environment(loader=FileSystemLoader(NcgConfig.config['templates']['root_dir']),trim_blocks=True)
    nginxconf = j2_env.get_template(NcgConfig.config['templates']['nginxconf']).render(declaration=d['declaration'])

    if type.lower() == "plaintext":
        # Plaintest output
        return nginxconf
    elif type.lower() == "json":
        # JSON-wrapped b64-encoded output
        b64NginxConf = str(base64.urlsafe_b64encode(nginxconf.encode("utf-8")), "utf-8")
        return JSONResponse(
            status_code=200,
            content={"nginx_config": f"{b64NginxConf}"}
        )
    elif type.lower() == 'configmap':
        # Kubernetes ConfigMap output
        cm = j2_env.get_template(NcgConfig.config['templates']['configmap']).render(nginxconfig=nginxconf,name=d['output']['configmap']['name'],filename=d['output']['configmap']['filename'])

        return Response(content=cm,headers={ 'Content-Type': 'application/x-yaml' })
    else:
        return JSONResponse(
            status_code=422,
            content={"message": f"output type {type} unknown"}
        )
