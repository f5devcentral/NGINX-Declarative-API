# Developer portal add-on

This is a wrapper for [Redocly CLI](https://redocly.com/docs/cli/) used by the NGINX declarative API to create and publish developer portals

To build:

	docker build --no-cache -t <YOUR_TARGET_IMAGE_NAME> .

To run the pre-built image:

	docker run --rm -d -p 5001:5000 --name devportal fiorucci/nginx-declarative-api-devportal

To test:

	curl -i -w '\n' 127.0.0.1:5001/v1/devportal -X POST -H "Content-Type: application/json" -d @<OPENAPI_JSON_SCHEMA_FILENAME>
