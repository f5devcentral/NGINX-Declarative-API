# Example prompts

These assume the `nginx-declarative-api` MCP server (this contrib module) is
connected and pointed at a running v5.7 instance.

## Create a new reverse proxy config

> Create a new NGINX One declaration named `petstore` that reverse-proxies
> `api.petstore.example.com` to the upstream `https://10.0.4.10:8443`, rate
> limits clients to 10 requests/second with a burst of 20, and publish it
> synchronously.

## Inspect what the instance actually supports

> What fields does this v5.7 instance's declaration schema support for TCP/UDP
> stream servers?

## Update an existing config asynchronously

> Update the `petstore` declaration to add a WAF policy fetched from
> `https://git.example.internal/policies/petstore-waf.json`, checked every 5
> minutes, and publish it asynchronously.

## Poll an async submission

> Check whether submission `3f9a1b2c-...` for `petstore` has finished
> publishing yet.

## Clean up

> Delete the `petstore` declaration.

## Ad-hoc / anything not covered by the curated tools

> Using the declarative API's developer portal endpoints, publish the OpenAPI
> spec at `https://git.example.internal/specs/petstore.yaml` as a developer
> portal entry for `petstore`.
