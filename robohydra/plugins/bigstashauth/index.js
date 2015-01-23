var heads               = require('robohydra').heads,
    RoboHydraHead       = require("robohydra").heads.RoboHydraHead,
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
                path: '/api/v1/tokens',
                handler: function(req, res, next) {
                    modules.assert.equal(req.method, "POST", "Token resource supports only POST")
                    if("authorization" in req.headers) {
                        var auth = req.headers["authorization"].split(" ");
                        modules.assert.equal(auth.length, 2, "client sent invalid auth");
                        modules.assert.equal(auth[0], "Basic", "client didn't send basic auth");
                        var b64creds = new Buffer(auth[1], 'base64'),
                            creds = b64creds.toString().split(":");
                        modules.assert.equal(creds.length, 2, "client sent invalid basic auth");
                        if (creds[0] == "test" && creds[1] == "test") {
                            res.statusCode = '200';
                            res.send(JSON.stringify(token));
                        } else {
                            res.authfail = true
                        }
                    }
                    if (res.hasOwnProperty('authfail')) {
                        res.headers["www-authenticate"] = 'Basic realm="foobar"';
                        res.statusCode = '401';
                        res.send("401 - Forbidden")
                    }
                    res.end();
                }
            })
//            new RoboHydraHead({
//                path: '/api/v1/test',
//                handler: function(req, res, next) {
//                    if("authorization" in req.headers) {
//                        var auth = req.headers["authorization"];
//                        modules.assert.ok('KeyId' in auth, "KeyId missing from signature auth header");
//                        modules.assert.ok('algorithm' in auth, "algorithm missing from signature auth header");
//                        modules.assert.ok('headers' in auth, "headers missing from signature auth header");
//                        modules.assert.ok('signature' in auth, "signature missing from signature auth header");
//                    }
//                    if (res.hasOwnProperty('authfail')) {
//                        res.headers["www-authenticate"] = 'Basic realm="foobar"';
//                        res.statusCode = '401';
//                        res.send("401 - Forbidden")
//                    } else {
//                        return next(req, res)
//                    }
//                }
//            })
        ],
        scenarios: {
            authFails: {
                instructions: "Authentication will fail",
                heads: [
                    new RoboHydraHead({
                        path: '/.*',
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
                        path: '/.*',
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

