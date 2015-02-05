#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from pymongo import MongoClient
from bottle import Bottle, request, abort, static_file

application = Bottle()

db = MongoClient()['buibui']['danmaku']
db.ensure_index('ts')


@application.route('/buibui/get_danmakus')
def get_danmakus():
    ts = int(request.params.ts)
    qset = list(db.find({'ts': {'$gt': ts}}))
    for i in qset:
        del i['_id']
    return {'danmakus': qset}

BUI_PARAMS = {
    'text': str,
    'mode': int,
    'color': str,
    'size': int,
}


@application.post('/buibui/bui')
def bui():
    data = request.params
    msg = {}
    for k, t in BUI_PARAMS.iteritems():
        v = data.get(k)
        if not v:
            abort(400, 'params error')
        msg[k] = t(v)
    msg['ts'] = int(time.time() * 1000)
    db.insert(msg)
    return 'ok'


@application.route('/bower_components/<path:path>')
def server_bower_components(path):
    return static_file(path, root='../web_client/bower_components')


@application.route('/player/<path:path>')
def player_src(path):
    return static_file(path, root='../web_player/src')


@application.route('/')
def server_index():
    return static_file('index.html', root='../web_client/src')


@application.route('/<path:path>')
def server_src(path):
    return static_file(path, root='../web_client/src')

if __name__ == '__main__':
    application.run(host='0.0.0.0', port=8080, debug=True, reloader=True)
