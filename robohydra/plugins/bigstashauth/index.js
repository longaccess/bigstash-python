var heads               = require('robohydra').heads,
    RoboHydraHead       = require("robohydra").heads.RoboHydraHead,
    RoboHydraHeadStatic = heads.RoboHydraHeadStatic, 
    apiPrefix           = require("./index.js").apiPrefix


exports.getBodyParts = function(config, modules) {
    var token = {
      key: "asdfkdsfldskldfsk", 
      secret: "sdfsdkfsdklsdfklds",
      name: "some name",
      url: "/api/v1/tokens/1",
      created: "some date"
    }
    return {
        heads: [
            new RoboHydraHead({
                path: '/.*',
                handler: function(req, res, next) {
                    if("authorization" in req.headers) {
                        var auth = req.headers["authorization"];
                        if (auth.indexOf("Signature") == 0){
                            var start = "Signature ";
                            var parts = auth.slice(start.length);
                            parts = parts.split(', ');
                            modules.assert.equal(parts[0].indexOf('keyId'), 0, "Missing keyId from signature");
                            modules.assert.equal(parts[0].indexOf('algorithm'), 0, "Missing algorithm form signature");
                            modules.assert.equal(parts[0].indexOf('headers'), 0, "Missing headers from signature");
                            modules.assert.equal(parts[0].indexOf('signature'), 0, "Missing signature from signature");
                            res.authuser = true;
                            return next(req, res);
                        } else if ((auth.indexOf("Basic") == 0) && (req.url == '/api/v1/tokens/')){
                            var parts = auth.split(" ");
                            modules.assert.equal(auth.length, 2, "client sent invalid auth");
                            modules.assert.equal(auth[0], "Basic", "client didn't send basic auth");
                            var b64creds = new Buffer(parts[1], 'base64'),
                                creds = b64creds.toString().split(":");
                            modules.assert.equal(creds.length, 2, "client sent invalid basic auth");
                            if (creds[0] == "test" && creds[1] == "test") {
                                res.authuser = true;
                                return next(req, res);
                            } else {
                                res.authfail = true;
                            } 
                        }
                    } else {
                        res.authfail = true
                    }
                    if (res.hasOwnProperty('authuser')) {
                        res.authfail = true
                    }
                    if (res.hasOwnProperty('authfail')) {
                        res.headers["www-authenticate"] = 'Basic realm="foobar"';
                        res.statusCode = '401';
                        res.send("401 - Forbidden");
                    } else {
                        return next(req, res)
                    }
                }
            }),
            new RoboHydraHeadStatic({
                path: '/api/v1/tokens/',
                content: token
            })
        ],
        scenarios: {
            authFails: {
                instructions: "Authentication will fail",
                heads: [
                    new RoboHydraHead({
                        path: '/tokens/',
                        handler: function(req, res, next) {
                            res.authfail = true;
                            next(req, res);
                        }
                    })
                ]
            },
            authUser: {
                instructions: "Authentication for user test with password test",
                heads: [
                    new RoboHydraHead({
                        path: '/tokens/',
                        handler: function(req, res, next) {
                            res.authuser = true;
                            next(req, res);
                        }
                    })
                ]
            }

        }
    };
};

