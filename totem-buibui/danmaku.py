# -*- coding: utf-8 -*-
from gi.repository import GObject
import threading
GObject.threads_init()


D_MODE_RIGHT2LEFT = 0
D_MODE_LEFT2RIGHT = 1
D_MODE_TOP = 2
D_MODE_BOTTOM = 3


class DanmakuStream(object):
    def __init__(self, url):
        self._url = url
        self._dummy_flag = False

    def get_danmakus(self, now):
        if self._dummy_flag:
            return []

        self._dummy_flag = True
        return [{
            "text": "hello world",
            'color': "#ffffff",
            "size": 25,
            'mode': D_MODE_LEFT2RIGHT
        },
            {
                "text": "hello world",
                'color': "#ffffff",
                "size": 25,
                'mode': D_MODE_LEFT2RIGHT
            }
        ]
