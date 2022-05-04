// NGINX Configuration Generator - JSON declaration validator

function declarationValidator(json) {
    const Ajv = require("ajv")
    const ajv = new Ajv({allErrors: true})

    const declarationSchema = {
      type: "object",
      properties: {

        output: {
            type: "object",
            properties: {
                type: { type: "string" }
            },
            required: [ "type" ]
        },

        declaration: {
            type: "object",
            properties: {
                servers: {
                    type: "array",
                    items: {
                        type: "object",
                        properties: {
                            names: {
                                type: "array",
                                items: {
                                    type: "string"
                                }
                            },
                            listen: {
                                type: "object",
                                properties: {
                                    address: { type: "string" },
                                    http2: { type: "boolean" },
                                    tls: { type: "object" }
                                },
                                required: []
                            },
                            log: {
                                type: "object",
                                properties: {
                                    access: { type: "string" },
                                    error: { type: "string" }
                                },
                                required: []
                            },
                            locations: {
                                type: "array",
                                items: {
                                    type: "object",
                                    properties: {
                                        uri: { type: "string" },
                                        urimatch: { type: "string", default: "prefix" },
                                        upstream: { type: "string" },
                                        caching: { type: "string" },
                                        rate_limit: {
                                            type: "object",
                                            properties: {
                                                profile: { type: "string", default: "" },
                                                httpcode: { type: "integer", default: 429 },
                                                burst: { type: "integer", default: 0 },
                                                delay: { type: "integer", default: 0 }
                                            }
                                        },
                                        health_check: { type: "boolean" },
                                        snippet: { type: "string" }
                                    },
                                    required: [ "uri" ]
                                }
                            },
                            snippet: { type: "string", default: "" }
                        },
                        required: []
                    }
                },
                upstreams: {
                    type: "array",
                    items: {
                        type: "object",
                        properties: {
                            name: { type: "string" },
                            origin: {
                                type: "array",
                                items: {
                                    type: "object",
                                    properties: {
                                        server: { type: "string" },
                                        weight: { type: "integer" },
                                        max_fails: { type: "integer" },
                                        fail_timeout: { type: "string" },
                                        max_conns: { type: "integer" },
                                        slow_start: { type: "string" },
                                        backup: { type: "boolean" }
                                    },
                                    required: [ "server" ]
                                }
                            },
                            sticky: {
                                type: "object",
                                properties: {
                                    cookie: { type: "string" },
                                    expires: { type: "string" },
                                    domain: { type: "string" },
                                    path: { type: "string" }
                                },
                                required: [ "cookie" ]
                            },
                            snippet: { type: "string", default: "" }
                        },
                        required: [ "name" ]
                    }
                },
                caching: { type: "array" },
                rate_limit: {
                    type: "array",
                    items: {
                        type: "object",
                        properties: {
                            name: { type: "string" },
                            key: { type: "string" },
                            size: { type: "string" },
                            rate:  { type: "string" }
                        },
                        required: [ "name", "key", "size", "rate" ]
                    }
                },
                nginx_plus_api: {
                    type: "object",
                    properties: {
                        write: { type: "boolean" },
                        listen: { type: "string" },
                        allow_acl: { type: "string" }
                    }
                }
            }
        }
      },
      required: [ "output", "declaration" ],
      additionalProperties: false,
    }

    const validate = ajv.compile(declarationSchema)

    const data = {
      detail: { test: 123 },
      foo: 1,
      bar: "ok"
    }

    const valid = validate(json)
    if (!valid) {
        return { "valid": false, "error": validate.errors }
    } else {
        return { "valid": true }
    }
}

module.exports = { declarationValidator }