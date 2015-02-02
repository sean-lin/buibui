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

    __slot__ = ['text', 'color', 'x', 'y', 'font', 'size']

    def __init__(self, text, color="#ffffff", size=25):
        self.text = text
        self.font_name = self.DEFAULT_FONT
        self.size = size

    def start(self, screen, width, height):
        raise NotImplementedError

    def tick(self, tick):
        raise NotImplementedError

    def get_font_string(self):
        return "%s %d" % (self.font_name, self.size)
    font = property(get_font_string)


class DanmakuRight2Left(Danmaku):
    def setup(self, s_width, s_height, width, height):
        self._s_width = s_width
        self._s_height = s_height
        self._width = width
        self._height = height

    def tick(self, tick):
        return True


class DanmakuStream(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port

    def get_danmuku():
        return DanmakuRight2Left("hello", start=100)
