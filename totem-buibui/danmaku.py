# -*- coding: utf-8 -*-
import time
import threading
import Queue
from gi.repository import GObject
import urllib
import json
GObject.threads_init()


D_MODE_RIGHT2LEFT = 0
D_MODE_LEFT2RIGHT = 1
D_MODE_TOP = 2
D_MODE_BOTTOM = 3


POLLING_PERIOD = 1


class PullingThread(threading.Thread):
    def __init__(self, url, queue):
        self._url = url
        self.running = False
        self.queue = queue
        self.last_time = time.time()
        super(PullingThread, self).__init__()

    def run(self):
        self.running = True
        while self.running:
            print 'pulling'
            msgs = self.request()
            for i in msgs:
                self.queue.put(i)
            time.sleep(POLLING_PERIOD)

    def stop(self):
        self.running = False

    def request(self):
        try:
            f = urllib.urlopen(self._url + '?ts=' + str(self.last_time))
            data = f.read()
            msg = self.parse_data(data)
            if msg:
                self.last_time = msg[-1]['ts']
        except Exception as e:
            print e
            return []

    def parse_data(self, data):
        msg = json.loads(data)
        msg = sorted(msg, key=lambda x: x['ts'])
        return msg


class DanmakuStream(object):
    def __init__(self, url):
        self._url = url
        self._dummy_flag = False
        self._queue = Queue.Queue()
        self._thread = PullingThread(self._url, self._queue)
        self._thread.start()

    def close(self):
        if self._thread.running:
            self._thread.stop()
            self._thread.join()

    def get_danmakus(self, now):
        out = []
        while True:
            try:
                msg = self._queue.get_nowait()
                out.append(msg)
            except Queue.Empty:
                break

        return out
