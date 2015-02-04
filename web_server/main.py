#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from pymongo import MongoClient
from bson.json_util import dumps
from bottle import Bottle, request, abort

application = Bottle()

db = MongoClient()['buibui']['danmaku']
db.ensure_index({'ts': 1})


@application.route('/buibui/get_danmakus')
def get_danmakus():
    ts = request.params.ts
    qset = db.find({'ts': {'$gt': ts}})
    return {'danmakus': [dumps(i) for i in qset]}

BUI_PARAMS = {
    'text': str,
    'mode': int,
    'color': str,
    'size': int,
}


@application.route('/buibui/bui')
def bui():
    data = request.params
    msg = {}
    for k, t in BUI_PARAMS.iteritems:
        v = data.get(k)
        if not isinstance(v, t):
            abort(400, 'params error')
        msg[k] = v
    msg['ts'] = time.time()
    db.insert(msg)
    return 'ok'

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080, debug=True, reloader=True)
