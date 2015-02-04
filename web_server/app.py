#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
from pymongo import MongoClient
from bson.json_util import dumps
from bottle import Bottle, request, abort

application = Bottle()

db = MongoClient()['buibui']['danmaku']


@application.route('/buibui/get_danmakus')
def get_danmakus():
    ts = request.params.ts
    qset = db.find({'ts': {'$gt': ts}})
    return [dumps(i) for i in qset]

BUI_PARAMS = {
    'text': str,
    'mode': int,
    'color': str,
    'size': int,
}


@application.route('/buibui/bui')
def bui():
    data = request.params.data
    msg = json.loads(data)
    for k, t in BUI_PARAMS.iteritems:
        v = msg.get(k)
        if not isinstance(v, t):
            abort(400, 'params error')
    msg['ts'] = time.time()
    db.insert(msg)
    return 'ok'
