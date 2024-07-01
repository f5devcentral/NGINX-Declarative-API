import pathlib
import uvicorn
import subprocess
import json
import uuid
import base64
import yaml
import random

from typing import Any, Dict, AnyStr, List, Union

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response, JSONResponse

app = FastAPI(
    title="NGINX App Protect WAF Compiler REST API",
    version="1.0.0",
    contact={"name": "GitHub", "url": "https://github.com/fabriziofiorucci/NAP-Compiler-REST-API"},
    description="REST API interface for NGINX App Protect WAF Compiler"
)

JSONObject = Dict[AnyStr, Any]
JSONArray = List[Any]
JSONStructure = Union[JSONArray, JSONObject]

globalSettings = {
  "waf-settings": {
    "cookie-protection": {
      "seed": "RANDOM_SEED_HERE"
    },
    "user-defined-signatures": [
      {
        "$ref": "file:///USER_SIGNATURES_FILE_HERE"
      }
    ]
  }
}


#
# Payload format: {"user-signatures": "<BASE64_ENCODED_USER_SIGNATURES_JSON>", "policy": "<BASE64_ENCODED_POLICY_JSON>"}
#
@app.post("/v1/compile/policy", status_code=200, response_class=JSONResponse)
def v1_compile_policy(response: Response, request: JSONStructure = None):
    if request:
        try:
            sessionUUID = uuid.uuid4()
            napPolicy = base64.b64decode(request['policy']).decode()
            userSigs = base64.b64decode(request['user-signatures']).decode()

            tmpFileBase = f"/tmp/{sessionUUID}"

            globalSettings['waf-settings']['cookie-protection']['seed'] = str(int(random.random()*100000000000000))
            globalSettings['waf-settings']['user-defined-signatures'][0]['$ref'] = f"file://{tmpFileBase}.uds.json"

            tmpFileGlobalSettings = f"{tmpFileBase}.globalsettings.json"
            tmpFileUserSigs = f"{tmpFileBase}.uds.json"
            tmpFilePolicy = f"{tmpFileBase}.policy.json"
            tmpFileBundle = f"{tmpFileBase}.tgz"

            tmpFile = open(tmpFileGlobalSettings, "w")
            tmpFile.write(json.dumps(globalSettings))
            tmpFile.close()

            tmpFile = open(tmpFileUserSigs, "w")
            tmpFile.write(userSigs)
            tmpFile.close()

            tmpFile = open(tmpFilePolicy, "w")
            tmpFile.write(napPolicy)
            tmpFile.close()

            output = subprocess.check_output(f"/opt/app_protect/bin/apcompile -global {tmpFileGlobalSettings} -p {tmpFilePolicy} -o {tmpFileBundle}", shell=True)

            with open(tmpFileBundle, 'rb') as file:
                napBundle = base64.b64encode(file.read())

            return JSONResponse (content={'status': 'success','message': json.loads(output.decode()), 'policy': json.loads(napPolicy), 'bundle': f'{napBundle.decode()}'}, status_code=200)
        except subprocess.CalledProcessError as e:
            return JSONResponse (content={'status': str(e), 'message': output}, status_code=400)
        finally:
            files = [tmpFileGlobalSettings, tmpFilePolicy, tmpFileBundle, tmpFileUserSigs]
            for f in files:
              fileToRemove = pathlib.Path(f)
              if fileToRemove.is_file():
                  fileToRemove.unlink()
    else:
        return JSONResponse (content={'status': 'invalid body'}, status_code=400)

#
# Payload format: {"logprofile": "<BASE64_ENCODED_LOG_PROFILE_JSON>"}
#
@app.post("/v1/compile/logprofile", status_code=200, response_class=JSONResponse)
def v1_compile_logprofile(response: Response, request: JSONStructure = None):
    if request:
        try:
            sessionUUID = uuid.uuid4()
            logProfile = base64.b64decode(request['logprofile']).decode()
            tmpFileBase = f"/tmp/{sessionUUID}"
            tmpFileLogProfile = f"{tmpFileBase}.logprofile.json"
            tmpFileBundle = f"{tmpFileBase}.tgz"
            tmpFile = open(tmpFileLogProfile,"w")
            tmpFile.write(logProfile)
            tmpFile.close()

            output = subprocess.check_output(f"/opt/app_protect/bin/apcompile -l {tmpFileLogProfile} -o {tmpFileBundle}", shell=True)

            with open(tmpFileBundle, 'rb') as file:
                napBundle = base64.b64encode(file.read())

            return JSONResponse (content={'status': 'success','message': json.loads(output.decode()), 'logprofile': json.loads(logProfile) ,'bundle': f'{napBundle.decode()}'}, status_code=200)
        except subprocess.CalledProcessError as e:
            return JSONResponse (content={'status': str(e)}, status_code=400)
        finally:
            files = [tmpFileLogProfile, tmpFileBundle]
            for f in files:
              fileToRemove = pathlib.Path(f)
              if fileToRemove.is_file():
                  fileToRemove.unlink()
    else:
        return JSONResponse (content={'status': 'invalid body'}, status_code=400)


#
# Payload format: {"bundle": "<BASE64_ENCODED_TGZ_BUNDLE>"}
#
@app.post("/v1/bundle/info", status_code=200, response_class=JSONResponse)
def v1_bundle_info(response: Response, request: JSONStructure = None):
    if request:
        try:
            sessionUUID = uuid.uuid4()
            if 'bundle' in request:
              napBundle = request['bundle']

              tmpFileBase = f"/tmp/{sessionUUID}"
              tmpFileBundle = f"{tmpFileBase}.bundle.tgz"
              tmpFile = open(tmpFileBundle,"wb")
              tmpFile.write(base64.b64decode(napBundle))
              tmpFile.close()

              output = subprocess.check_output(f"/opt/app_protect/bin/apcompile -dump -bundle {tmpFileBundle}", shell=True)
              jsonOutput = yaml.safe_load(output.decode('utf-8'))
              jsonOutput['timestamp'] = f"{jsonOutput['timestamp']}"

              return JSONResponse (content={'status': 'success','message': jsonOutput}, status_code=200)
            else:
              raise ValueError('Invalid JSON format')
        except subprocess.CalledProcessError as e:
            return JSONResponse (content={'status': str(e)}, status_code=400)
        except ValueError as e:
            return JSONResponse (content={'status': str(e)}, status_code=400)
        finally:
            try:
              bundleFile = pathlib.Path(tmpFileBundle)
              if bundleFile.is_file():
                  bundleFile.unlink()
            except Exception:
              pass
    else:
        return JSONResponse (content={'status': 'invalid body'}, status_code=400)


if __name__ == '__main__':
    uvicorn.run("server:app", host='0.0.0.0', port=5000)
