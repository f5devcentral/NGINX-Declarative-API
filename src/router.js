var nunjucks = require('nunjucks')

var express = require('express')
var router = express.Router()


router.post('/config', express.json(), function(req, res, next) {
    nunjucks.configure(config.templates.root_dir,{ autoescape: true })
    var nginxconf = nunjucks.render(config.templates.nginxconf, req.body)

    var type = String(req.body.output.type).toLowerCase()

    if (type === 'plaintext') {
        res.status(200).send(nginxconf)
    } else if (type === 'json' || type === 'http') {
        // JSON-wrapped b64-encoded output
        var nginxConfBuffer = Buffer.from(nginxconf,'utf-8')
        var b64NginxConf = nginxConfBuffer.toString('base64')

        var payload = { nginx_config: b64NginxConf }

        if (type === 'json') {
            // Base64-encoded, JSON-wrapped output
            res.status(200).send(payload)
        } else {
            // Base64-encoded, JSON-wrapped output, POSTed to custom URL
            var request = require('request');

            request.post(
                {
                    url: req.body.output.http.url,
                    json: payload,
                    headers: {
                        'Content-Type': 'application/json'
                    }
                },
                function(error,response,body) {
                    res.status(response.statusCode).send(body)
                }
            )
        }
    } else if (type === 'configmap') {
        // Kubernetes ConfigMap output
        var cm = nunjucks.render(config.templates.configmap, { name: req.body.output.configmap.name, filename: req.body.output.configmap.filename, nginxconfig: nginxconf })
        res.status(200).send(cm)
    } else {
        res.status(422).send({'message': 'output type '+type+' unknown'})
    }
})

module.exports = router