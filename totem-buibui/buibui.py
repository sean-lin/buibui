import time
from gi.repository import GtkClutter    # pylint: disable=W0611
from gi.repository import GObject, Peas, GLib, Clutter
import danmaku


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
        self._dm.set_stream('http://127.0.0.1/')

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


class Danmaku(Clutter.Group):
    DEFAULT_FONT = 'SimHei'

    def __init__(self, text, color="#ffffff", size=25):
        super(Danmaku, self).__init__()

        # orgion configure
        self.text = text
        self.color = color
        self.font_name = self.DEFAULT_FONT
        self.size = size

        # runtime value
        self.duration = 0
        self.x = None
        self.y = None
        self._s_width = None
        self._s_height = None

        # clutters
        self._shadowBR = self.build_shadow(+2, +2)
        self._shadowTL = self.build_shadow(-2, -2)
        self._shadowBL = self.build_shadow(-2, +2)
        self._shadowTR = self.build_shadow(+2, -2)
        self._drawObject = self.build_text_clutter(self.color, 0, 0)

        self.width = self._drawObject.get_width() + 2
        self.height = self._drawObject.get_height() + 2

    def setup_ctx(self, s_width, s_height):
        self._s_width = s_width
        self._s_height = s_height
        return self

    def start(self):
        raise NotImplementedError

    def update(self, duration):
        raise NotImplementedError

    def tick(self, duration):
        self.duration += duration
        if self.update(duration):
            self.set_position(self.x, self.y)
            return True
        else:
            return False

    def get_font_string(self):
        return "%s %d" % (self.font_name, self.size)

    def build_shadow(self, x, y):
        return self.build_text_clutter("#000000", x, y)

    def build_text_clutter(self, color, x, y):
        shadow = Clutter.Text()
        shadow.set_color(Clutter.Color.from_string(color)[1])
        shadow.set_text(self.text)
        shadow.set_font_name(self.get_font_string())
        shadow.set_position(x, y)
        self.add_child(shadow)
        return shadow

DANMAKU_TTL = 5000


class DanmakuRight2Left(Danmaku):
    mode = danmaku.D_MODE_RIGHT2LEFT

    def start(self):
        self.x = self._s_width
        self.speed = self._s_width * 1.0 / DANMAKU_TTL
        return self

    def update(self, duration):
        self.x -= self.speed * duration
        if self.x + self.width < 0:
            return False
        return True


class DanmakuLeft2Right(Danmaku):
    mode = danmaku.D_MODE_LEFT2RIGHT

    def start(self):
        self.x = - self.width
        self.speed = self._s_width * 1.0 / DANMAKU_TTL
        return self

    def update(self, duration):
        self.x += 1
        if self.x > self._s_width:
            return False
        return True


class DanmakuTop(Danmaku):
    mode = danmaku.D_MODE_TOP

    def start(self):
        self.x = int((self._s_width - self.width) / 2)
        return self

    def update(self, duration):
        return self.duration < DANMAKU_TTL


class DanmakuBottom(Danmaku):
    mode = danmaku.D_MODE_BOTTOM

    def start(self):
        self.x = int((self._s_width - self.width) / 2)
        return self

    def update(self, duration):
        return self.duration < DANMAKU_TTL


HORIZONTAL_PADDING = 20


class AllocaotrLayerBase(object):
    def __init__(self, offset):
        self.offset = offset
        self.pool = set()

    def allocate(self, dmk):
        base_line = self.get_slots()
        y = self.offset
        for i in base_line:
            if i.y > y and i.y > dmk.height + y:
                dmk.y = y
                self.pool.add(dmk)
                return True
            y = i.y + i.height + 1
        return False

    def free(self, dmk):
        if dmk in self.pool:
            self.pool.remove(dmk)
            return True
        return False

    def setup_ctx(self, width, height):
        self.width = width
        self.height = height

    def get_slots(self):
        raise NotImplementedError


class DummyDanmaku(object):
    def __init__(self, offset):
        self.y = offset
        self.height = 0


class AllocaotrLayerRight2Left(AllocaotrLayerBase):
    def get_slots(self):
        base_line = [i for i in self.pool if self.conflict_start(i)]
        base_line.append(DummyDanmaku(self.height))
        return sorted(base_line, key=lambda x: x.y)

    def conflict_start(self, dmk):
        return dmk.width + dmk.x + HORIZONTAL_PADDING > self.width


class AllocaotrLayerLeft2Right(AllocaotrLayerBase):
    def get_slots(self):
        base_line = [i for i in self.pool if self.conflict_start(i)]
        base_line.append(DummyDanmaku(self.height))
        return sorted(base_line, key=lambda x: x.y)

    def conflict_start(self, dmk):
        return dmk.x - HORIZONTAL_PADDING < 0


class AllocaotrLayerTop(AllocaotrLayerBase):
    def get_slots(self):
        base_line = list(self.pool)
        base_line.append(DummyDanmaku(self.height))
        return sorted(base_line, key=lambda x: x.y)


class AllocaotrLayerBottom(AllocaotrLayerBase):
    def allocate(self, dmk):
        base_line = self.get_slots()
        y = self.height - dmk.height - self.offset
        for i in base_line:
            if i.y + i.height < y and i.y < y:
                dmk.y = y
                self.pool.add(dmk)
                return True
            y = i.y - dmk.height - 1
        return False

    def get_slots(self):
        base_line = list(self.pool)
        base_line.append(DummyDanmaku(0))
        return sorted(base_line, key=lambda x: x.y, reverse=True)


class Allocaotr(object):
    def __init__(self, layer_cls):
        self.layers = {}
        self.layer_cls = layer_cls
        self.width = None
        self.height = None

    def allocate(self, dmk):
        for i in self.layers:
            if self.layers[i].allocate(dmk):
                return
        idx = len(self.layers)
        offset = self.gen_offset(idx)
        self.layers[idx] = self.layer_cls(offset)
        self.layers[idx].setup_ctx(self.width, self.height)

        self.layers[idx].allocate(dmk)

    def free(self, dmk):
        for i in self.layers.values():
            if i.free(dmk):
                return True
        return False

    def gen_offset(self, idx):
        return idx * 15 % self.height

    def setup_ctx(self, width, height):
        self.width = width
        self.height = height
        for i in self.layers.values():
            i.setup_ctx(width, height)


DANMAKU_MAP = {
    danmaku.D_MODE_RIGHT2LEFT: DanmakuRight2Left,
    danmaku.D_MODE_LEFT2RIGHT: DanmakuLeft2Right,
    danmaku.D_MODE_BOTTOM: DanmakuBottom,
    danmaku.D_MODE_TOP: DanmakuTop,
}
ALLOCATOR_MAP = {
    danmaku.D_MODE_RIGHT2LEFT: Allocaotr(AllocaotrLayerRight2Left),
    danmaku.D_MODE_LEFT2RIGHT: Allocaotr(AllocaotrLayerLeft2Right),
    danmaku.D_MODE_BOTTOM: Allocaotr(AllocaotrLayerBottom),
    danmaku.D_MODE_TOP: Allocaotr(AllocaotrLayerTop),
}


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

    def set_stream(self, url):
        self._stream = danmaku.DanmakuStream(url)

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
                allocator = ALLOCATOR_MAP.get(i.mode)
                allocator.free(i)

        self._danmakus = new_danmakus
        self.last_time = now
        return True

    def tick(self, tick):
        dmks = self._stream.get_danmakus(tick)
        for i in dmks:
            dmk_obj = self.danmaku_builder(i)
            self.add_child(dmk_obj)
            self._danmakus.append(dmk_obj)

    def state_change(self, *arg):
        self.set_bounds()
        return False

    def set_bounds(self, *arg):
        stage = self.get_stage()

        if self.height == stage.get_height() and\
                self.width == stage.get_width():
            return

        self.height = stage.get_height()
        self.width = stage.get_width()

        # Set actor dimensions
        self.set_position(0, 0)
        self.set_size(self.width, self.height)

        map(
            lambda x: x.setup_ctx(self.width, self.height),
            ALLOCATOR_MAP.values()
        )
        [i.setup_ctx(self.width, self.height) for i in self._danmakus]
        return False

    def danmaku_builder(self, cfg):
        mode = cfg['mode']
        dmk_cls = DANMAKU_MAP.get(mode)
        if not dmk_cls:
            raise NotImplementedError
        dmk = dmk_cls(cfg['text'], cfg.get('color'), cfg.get('size'))
        dmk.setup_ctx(self.width, self.height).start()

        allocator = ALLOCATOR_MAP.get(mode)
        allocator.allocate(dmk)
        return dmk
