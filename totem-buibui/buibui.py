import time
from gi.repository import GLib, GObject, Peas, Clutter
from danmaku import DanmakuStream


class DanmukuWraper(Clutter.Group):
    def __init__(self, dmk):
        self.dmk = dmk
        text = Clutter.Text()
        text.set_color(Clutter.Color.from_string(dmk.color)[1])
        text.set_text(dmk.text)
        text.set_font_name(dmk.font)
        self._drawObject = text
        self.add_child(text)

        self._shadowBR = self.build_shadow(dmk, +1, +1)
        self._shadowTL = self.build_shadow(dmk, -1, -1)
        self._shadowBL = self.build_shadow(dmk, -1, +1)
        self._shadowTR = self.build_shadow(dmk, +1, -1)

        self._width = dmk._drawObject.get_width() + 1
        self._height = dmk._drawObject.get_height() + 1

    def build_shadow(self, dmk, x, y):
        shadow = Clutter.Text()
        shadow.set_color(Clutter.Color.from_string("#000000")[1])
        shadow.set_text(dmk.text)
        shadow.set_font_name(dmk.font)
        shadow.set_position(x, y)
        self.add_child(shadow)

    def tick(self):
        if self.dmk.tick():
            self.set_position(self.dmk.x, self.dmk.y)
            return True
        else:
            return False


class DanmakuManager(Clutter.Actor):
    def __init__(self, screen):
        self._last_tick = 0
        self._screen = screen
        self._danmukus = []

        self.width = None
        self.height = None

        self.is_playing = False
        #GLib.timeout_add(20, self.timer)

    def set_stream(self, host, port):
        self._stream = DanmakuStream(host, port)

    def resume(self):
        self.is_playing = True

    def stop(self):
        self.is_playing = False

    def clear(self):
        for dmk in self._danmuku:
            self.remove_child(dmk)
        self._danmuku = []

    def timer(self, time):
        if not self.is_playing:
            return True
        self._danmuku = [
            i for i in self._danmuku if i.tick()
        ]
        return True

    def tick(self, now):
        pass

    def state_change(self, *arg):
        self.set_bounds()
        return False

    def set_bounds(self, *arg):
        stage = self.get_stage()

        s_height = stage.get_height()
        s_width = stage.get_width()
        self.width = s_width
        self.height = s_height

        # Set actor dimensions
        self.set_position(0, 0)
        self.set_size(s_width, s_height)
        return False


class Buibui(GObject.Object, Peas.Activatable):
    __gtype_name__ = 'Buibui'

    object = GObject.property(type=GObject.Object)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self._totem = self.object

        video = self._totem.get_video_widget()
        self._dm = DanmakuManager(self._totem)

        video.get_stage().add_child(self._dm)
        video.get_toplevel().connect(
            "window-state-event", self._dm.state_change)
        video.get_toplevel().connect("configure-event", self._dm.set_bounds)
        video.connect("size-allocate", self._dm.set_bounds)

        # add signal to update the danmaku stage
        self._tick_signal_handler = video.connect("tick", self.tick_handler)
        self._play_signal_handler = self._totem.connect(
            "file-has-played", self.play_handler)
        self._end_signal_handler = video.connect("eos", self.end_handler)

    def do_deactivate(self):
        self._totem = None

    def play_handler(self, murl, user_data):
        self._dm.resume()

    def tick_handler(self, video, cur_time, st_length, cur_pos, user_data):
        if self._totem.is_playing():
            if not self._cm.is_playing:
                self._cm.resume()
        else:
            self._cm.stop()
        print cur_time, st_length, cur_pos
        self._cm.tick(cur_time)

    def end_handler(self, user_data):
        self._dm.stop()
        self._dm.clear()
