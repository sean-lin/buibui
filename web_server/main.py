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

TEXT_MAX = 72
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
    msg['user'] = request.get_header('X-Ldap-User')
    msg['ts'] = int(time.time() * 1000)
    
    text = msg['text']
    for i in range(0, len(text), TEXT_MAX):
        splited = msg.copy()
        splited['text']  = text[i:i + TEXT_MAX]
        db.insert(splited)
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
