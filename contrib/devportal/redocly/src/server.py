import pathlib
import uvicorn
import subprocess
import json
import uuid

from typing import Any, Dict, AnyStr, List, Union

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response, JSONResponse

app = FastAPI(
    title="Redocly connector",
    version="1.0.0",
    contact={"name": "GitHub", "url": "https://github.com/f5devcentral/NGINX-Declarative-API"}
)

JSONObject = Dict[AnyStr, Any]
JSONArray = List[Any]
JSONStructure = Union[JSONArray, JSONObject]

@app.post("/v1/devportal", status_code=200, response_class=JSONResponse)
def post_devportal(response: Response, request: JSONStructure = None):
    if request:
        try:
            sessionUUID = uuid.uuid4()
            apiSchema = json.dumps(request)
            tmpFileBase = f"/tmp/{sessionUUID}"
            tmpFileSchema = f"{tmpFileBase}.json"
            tmpFileDocs = f"{tmpFileBase}.html"
            tmpFile = open(tmpFileSchema,"w")
            tmpFile.write(apiSchema)
            tmpFile.close()

            output = subprocess.check_output(f"redocly build-docs '{tmpFileSchema}' --output={tmpFileDocs}", shell=True)

            with open(tmpFileDocs, 'r') as file:
                devPortal = file.read().replace('\n','')

            return JSONResponse (content={'status': 'success','apischema': f'{apiSchema}','devportal': f'{devPortal}'}, status_code=200)
        except subprocess.CalledProcessError as e:
            return JSONResponse (content={'status': str(e)}, status_code=400)
        finally:
            schemaFile = pathlib.Path(tmpFileSchema)
            if schemaFile.is_file():
                schemaFile.unlink()

            docsFile = pathlib.Path(tmpFileDocs)
            if docsFile.is_file():
                docsFile.unlink()
    else:
        return JSONResponse (content={'status': 'invalid body'}, status_code=400)

if __name__ == '__main__':
    uvicorn.run("server:app", host='0.0.0.0', port=5000)
