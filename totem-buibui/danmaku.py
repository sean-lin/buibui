# -*- coding: utf-8 -*-
from gi.repository import GObject
import threading
GObject.threads_init()

D_MODE_RIGHT2LEFT = 0
D_MODE_LEFT2RIGHT = 1
D_MODE_TOP = 2
D_MODE_BOTTOM = 3


class Danmaku(object):
    DEFAULT_FONT = 'SimHei'

    __slot__ = ['text', 'color', 'x', 'y', 'font', 'size', 'stime', 'ctx']

    def __init__(self, text, color="#ffffff", size=25):
        self.text = text
        self.color = color
        self.font_name = self.DEFAULT_FONT
        self.size = size
        self.stime = None
        self.x = None
        self.y = None

    def start(self, now):
        self.stime = now
        return self

    def setup_ctx(self, s_width, s_height):
        self.ctx = {"width": s_width, "height": s_height}
        return self

    def get_font_string(self):
        return "%s %d" % (self.font_name, self.size)
    font = property(get_font_string)

    def tick(self, tick):
        raise NotImplementedError


class DanmakuRight2Left(Danmaku):
    def tick(self, now):
        if self.x == None or self.y == None:
            self.x = self.ctx['width']
            self.y = 100

        self.x -= 1
        if self.x == 0:
            print 'clean'
            return False
        return True


class DanmakuStream(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._dummy_flag = False

    def get_danmakus(self, now):
        if self._dummy_flag:
            return []

        self._dummy_flag = True
        return [DanmakuRight2Left("hello world")]
