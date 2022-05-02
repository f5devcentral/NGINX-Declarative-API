// NGINX Configuration Generator
var express = require('express')
var http = require('http')

var api_v0 = require('./router.js')
var app = express()
var server = http.createServer(app)

// Configuration file
const fs = require('fs')
const toml = require('toml')
global.config = toml.parse(fs.readFileSync('../etc/config.toml', 'utf-8'))

console.log('%s %s',config.main.banner,config.main.version)

// Webserver initialization
app.use('/v0',api_v0)

server.listen(config.apiserver.port, config.apiserver.host, () => console.log('Started API server on %s:%s', server.address().address, server.address().port))