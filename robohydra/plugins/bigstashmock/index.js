var heads               = require('robohydra').heads,
    RoboHydraHead       = require("robohydra").heads.RoboHydraHead,
    RoboHydraHeadStatic = heads.RoboHydraHeadStatic,
    token               = require('./tokens.js').token,
    apiPrefix           = "/api/v1";


exports.getBodyParts = function(config, modules) {
  archives = {
    'Photos': {
      "id": 1,
      "status" : "creating",
      "key" : "58-CXSS2Q",
      "size" : 50000,
      "checksum" : null,
      "created" : "2014-06-30T17:01:21.887Z",
      "url" : "http://stage.deepfreeze.io/api/v1/archives/58/",
      "upload" : "http://stage.deepfreeze.io/api/v1/archives/58/upload/",
      "title": "some title"
    },
    'Other': {
      "id": 2,
      "status" : "creating",
      "key" : "58-CXSS2Q",
      "size" : 50000,
      "checksum" : null,
      "created" : "2014-06-30T17:01:21.887Z",
      "url" : "http://stage.deepfreeze.io/api/v1/archives/58/",
      "upload" : "http://stage.deepfreeze.io/api/v1/archives/58/upload/",
      "title": "some title"
    }
  }
  function meta(n){
    return {
      limit: 20,
      next: null,
      offset: 0,
      previous: null,
      total_count: n
    }
  }
  return {
    heads: [
      new RoboHydraHeadStatic({
        path: apiPrefix + '/archives/',
        content: {
          meta: meta(2),
          results: [
            archives.Photos,
            archives.Other
          ]
        }
      }),
      new RoboHydraHeadStatic({
        path: apiPrefix + '/archives/1/',
        content: {
            archives.Other
        }
      })  
    ]
  }
}
