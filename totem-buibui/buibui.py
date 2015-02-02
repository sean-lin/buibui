import time
from gi.repository import GObject, Peas, Gtk, GLib, GtkClutter, Clutter
from danmaku import DanmakuStream


class Buibui(GObject.Object, Peas.Activatable):
    __gtype_name__ = 'Buibui'

    object = GObject.property(type=GObject.Object)

    def __init__(self):
        GObject.Object.__init__(self)
        self._totem = None

    def do_activate(self):
        self._totem = self.object

        video = self._totem.get_video_widget()
        self._dm = DanmakuManager(self._totem)
        self._dm.set_stream('127.0.0.1', 80)

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
            if not self._dm.is_playing:
                self._dm.resume()
            self._dm.tick(cur_time)
        else:
            self._dm.stop()

    def end_handler(self, user_data):
        self._dm.stop()
        self._dm.clear()


class DanmakuWrapper(Clutter.Group):
    def __init__(self, dmk):
        super(DanmakuWrapper, self).__init__()
        self.dmk = dmk
        text = Clutter.Text()
        text.set_color(Clutter.Color.from_string(dmk.color)[1])
        text.set_text(dmk.text)
        text.set_font_name(dmk.font)
        self._drawObject = text

        self._shadowBR = self.build_shadow(dmk, +1, +1)
        self._shadowTL = self.build_shadow(dmk, -1, -1)
        self._shadowBL = self.build_shadow(dmk, -1, +1)
        self._shadowTR = self.build_shadow(dmk, +1, -1)

        self.add_child(text)

        self._width = self._drawObject.get_width() + 1
        self._height = self._drawObject.get_height() + 1

    def build_shadow(self, dmk, x, y):
        shadow = Clutter.Text()
        shadow.set_color(Clutter.Color.from_string("#000000")[1])
        shadow.set_text(dmk.text)
        shadow.set_font_name(dmk.font)
        shadow.set_position(x, y)
        self.add_child(shadow)

    def tick(self, now):
        if self.dmk.tick(now):
            self.set_position(self.dmk.x, self.dmk.y)
            return True
        else:
            return False


class DanmakuManager(Clutter.Actor):
    def __init__(self, screen):
        super(DanmakuManager, self).__init__()
        self._last_tick = 0
        self._screen = screen
        self._danmakus = []

        self.width = None
        self.height = None

        self.is_playing = False
        self.last_time = time.time() * 1000

        GLib.timeout_add(20, self.timer)

    def set_stream(self, host, port):
        self._stream = DanmakuStream(host, port)

    def resume(self):
        self.is_playing = True

    def stop(self):
        self.is_playing = False

    def clear(self):
        for dmk in self._danmakus:
            self.remove_child(dmk)
        self._danmakus = []

    def timer(self, *args):
        if not self.is_playing:
            self.last_time = time.time() * 1000
            return True
        now = time.time() * 1000
        duration = now - self.last_time
        new_danmakus = []
        for i in self._danmakus:
            if i.tick(duration):
                new_danmakus.append(i)
            else:
                self.remove_child(i)
        self._danmakus = new_danmakus
        self.last_time = now
        return True

    def tick(self, tick):
        now = time.time() * 1000
        dmks = self._stream.get_danmakus(tick)
        dmks = [DanmakuWrapper(
            i.setup_ctx(self.width, self.height).start(now))
            for i in dmks
        ]
        [self.add_child(i) for i in dmks]
        self._danmakus.extend(dmks)

    def state_change(self, *arg):
        self.set_bounds()
        return False

    def set_bounds(self, *arg):
        stage = self.get_stage()

        self.width = stage.get_height()
        self.height = stage.get_width()

        # Set actor dimensions
        self.set_position(0, 0)
        self.set_size(self.width, self.height)
        return False
