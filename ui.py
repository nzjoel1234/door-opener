import machine
import utime
import framebuf
import ssd1306
import _thread
from workScheduler import WorkScheduler


instance = None


def setup(i2c):
    global instance
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
    instance = UiManager(oled)
    return instance


def draw_small_up_arrow(oled, x, y, c):
    for i in range(0, 4):
        oled.hline(x + 3 - i, y + i, i * 2 + 1, c)


def draw_small_down_arrow(oled, x, y, c):
    for i in range(0, 4):
        oled.hline(x + i, y + 5 + i, 7 - i * 2, c)


def draw_prev_arrow(oled, y):
    for i in range(0, 5):
        oled.hline(63 - i, y + i + 1, (i + 1) * 2, 1)


def draw_next_arrow(oled):
    for i in range(0, 5):
        oled.hline(63 - i, 63 - i, (i + 1) * 2, 1)


def multi_line_text(oled, text, y):
    import math
    for line in range(math.ceil(len(text) / 16)):
        start = line * 16
        end = start + 16
        oled.text(text[start:end], 0, y + line * 10)


def centered_text(oled, text, y):
    oled.text(text, 64 - (len(text) * 4), y)


def text_right(oled, text, x, y):
    oled.text(text, x - (len(text) * 8), y)


def move_index(delta, index, items):
    nex_index = index + delta
    return min(len(items) - 1, nex_index) if delta > 0 else max(0, nex_index)


class UiManager:

    def __init__(self, oled):
        self.oled = oled
        self.current_control = None
        self.scheduler = WorkScheduler()
        self.goto(LoadingControl(self))
        self.lock = _thread.allocate_lock()

    def goto(self, new_control):
        self.current_control = new_control
        self.schedule_render()

    def schedule_render(self, millis=0):
        self.scheduler.schedule_work(millis)

    def do_tasks(self):
        try:
            if not self.scheduler.work_pending():
                return
            self.render_scheduled = False
            self.current_control.render(self.oled)
        except Exception as e:
            print('render error: {}'.format(repr(e)))
            self.scheduler.schedule_work(2000)  # Try render again in 2 seconds

    def on_up(self):
        with self.lock:
            self.current_control.on_up()

    def on_down(self):
        with self.lock:
            self.current_control.on_down()

    def on_select(self):
        with self.lock:
            self.current_control.on_select()


class UiControl:

    def __init__(self, ui):
        self.ui = ui

    def on_up(self):
        pass

    def on_down(self):
        pass

    def on_select(self):
        pass

    def render(self, oled):
        pass


class LoadingControl(UiControl):

    def __init__(self, ui):
        super().__init__(ui)
        self.status = ''
        self.detail = ''

    def set_status(self, status):
        self.status = status
        self.detail = ''
        self.ui.schedule_render()

    def set_detail(self, detail):
        self.detail = detail
        self.ui.schedule_render()

    def render(self, oled):
        y, mo, d, h, mi, s, *rest = utime.localtime()
        oled.fill(0)
        centered_text(oled, 'Loading...', 0)
        centered_text(oled, self.status, 10)
        multi_line_text(oled, self.detail, 20)
        oled.show()


week_day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


class DashboardControl(UiControl):

    def __init__(self, ui):
        super().__init__(ui)

    def get_this(self):
        return DashboardControl(self.ui)

    def on_select(self):
        self.ui.goto(MenuControl.get_root_menu(
            self.ui, lambda: DashboardControl(self.ui)))

    @staticmethod
    def get_rssi():
        rssi = None
        try:
            import wifiConnect
            status = wifiConnect.getStatus()
            if status['active']:
                rssi = status['rssi']
        except Exception as e:
            print('Dashboard failed to get rssi: {}'.format(repr(e)))
        return rssi

    @staticmethod
    def rssi_to_sig_strength(rssi):
        if rssi is None:
            return 0
        if rssi > -45:
            return 3
        if rssi > -70:
            return 2
        return 1

    def render(self, oled):

        oled.fill(0)

        rssi = DashboardControl.get_rssi()
        sig_strength = DashboardControl.rssi_to_sig_strength(rssi)

        screen_w = 128
        max_bar_height = 7
        bar_width = 4
        bar_space = 1
        num_bars = 3
        first_bar_x = screen_w - num_bars * (bar_width + bar_space)

        bars = map(lambda i: {
            'fill': sig_strength > i,
            'x': first_bar_x + i * (bar_width + bar_space),
            'h': 1 if sig_strength <= i else max_bar_height - 2 * (num_bars - 1 - i),
        }, range(num_bars))

        for bar in bars:
            # f = oled.fill_rect if bar['fill'] else oled.rect
            # x, y, w, h, c
            y = max_bar_height - bar['h']
            oled.fill_rect(bar['x'], y, bar_width, bar['h'], 1)

        text_right(oled, '--' if rssi is None else str(rssi),
                   first_bar_x - 2, 0)

        y, mo, d, h, mi, s, wd, yd = utime.localtime()

        week_day = week_day_labels[wd]
        oled.text('{:02d}:{:02d}'.format(h, mi), 0, 0)

        centered_text(oled, '{} {:02d}-{:02d}-{:02d}'.format(
            week_day, d, mo, y % 100), 20)
        oled.show()
        self.ui.schedule_render(min(10000, (60 - s) * 1000 + 100))


class MenuControl(UiControl):

    def __init__(self, ui, title, items):
        super().__init__(ui)
        self.index = 0
        self.direction_down = True
        self.title = title
        self.items = items

    def render(self, oled):
        index = self.index
        num_lines = 4
        up_arrow_y = 11
        first_line_y = up_arrow_y + 7
        first_line = 0

        if len(self.items) > num_lines:
            if self.direction_down and index > 2:
                first_line = index - 2
            if not self.direction_down and index > 1:
                first_line = index - 1
            if first_line + num_lines > len(self.items):
                first_line = len(self.items) - num_lines

        oled.fill(0)

        centered_text(oled, self.title, 1)

        # draw arrows to indicate if there are any off-screen items
        has_more_before = first_line > 0
        if has_more_before:
            draw_prev_arrow(oled, up_arrow_y)

        has_more_after = first_line + num_lines < len(self.items)
        if has_more_after:
            draw_next_arrow(oled)

        for page_line in range(0, min(num_lines, len(self.items))):
            item_index = first_line + page_line
            item_label = self.items[item_index][0]
            text_color = 1
            line_y = first_line_y + page_line * 10
            if item_index == index:
                text_color = 0
                oled.fill_rect(0, line_y - 1, 128, 10, 1)

            is_str = isinstance(item_label, str)
            text = item_label if is_str else item_label[0]
            r_text = None if is_str else item_label[1]
            adjustable_up = not is_str and len(
                item_label) >= 4 and item_label[2]
            adjustable_down = not is_str and len(
                item_label) >= 4 and item_label[3]

            max_text_len = 15 if adjustable_up or adjustable_down else 16
            if r_text and len(r_text) > 0:
                r_text_len = min(len(r_text), max_text_len)
                l_text_len = max(0, max_text_len - r_text_len - 1)
                l_text = '{{:<{}}}'.format(
                    l_text_len).format(text[:l_text_len])
                text = '{} {}'.format(l_text, r_text[:r_text_len])
                print('t: {} #{} ({}-{})'.format(
                    text, len(text), r_text_len, l_text_len))
            text = text[:max_text_len]
            if adjustable_up:
                draw_small_up_arrow(oled, 120, line_y - 1, text_color)
            if adjustable_down:
                draw_small_down_arrow(oled, 120, line_y, text_color)

            oled.text(text, 0, line_y, text_color)
        oled.show()

    def on_down(self):
        self.direction_down = True
        self.index = move_index(1, self.index, self.items)
        self.ui.schedule_render()

    def on_up(self):
        self.direction_down = False
        self.index = move_index(-1, self.index, self.items)
        self.ui.schedule_render()

    def on_select(self):
        self.items[self.index][1]()

    @staticmethod
    def get_root_menu(ui, get_root):
        def get_this(): return MenuControl.get_root_menu(ui, get_root)
        return MenuControl(ui, 'Main Menu', [
            ('Back', lambda: ui.goto(get_root())),
            ('Programs', lambda: ui.goto(
                MenuControl.get_programs_menu(ui, get_root=get_this))),
            ('Manual Run', lambda: ui.goto(ManualRunControl(ui, get_root=get_this))),
            ('Info', lambda: ui.goto(
                MenuControl.get_info_menu(ui, get_root=get_this))),
        ])

    @staticmethod
    def get_info_menu(ui, get_root):
        def get_this(): return MenuControl.get_info_menu(ui, get_root)
        return MenuControl(ui, 'Info', [
            ('Back', lambda: ui.goto(get_root())),
            ('WiFi Status', lambda: ui.goto(
                WifiStatusControl(ui, get_root=get_this))),
            ('AP Status', lambda: ui.goto(
                ApStatusControl(ui, get_root=get_this))),
            ('Server Status', lambda: ui.goto(
                ServerStatusControl(ui, get_root=get_this))),
        ])

    @staticmethod
    def get_programs_menu(ui, get_root):
        def get_this(): return MenuControl.get_programs_menu(ui, get_root)
        from sprinklerConfiguration import instance as config
        return MenuControl(ui, 'Programs', [
            ('Back', lambda: ui.goto(get_root())),
        ] + list(map(
            lambda program: (
                program[1],
                lambda program=program: ui.goto(
                    MenuControl.get_program_menu(ui, program, get_root=get_this))),
            config.get_programs() if config else [])))

    @staticmethod
    def get_program_menu(ui, program, get_root):
        def start():
            from scheduler import instance as scheduler
            if not scheduler:
                return
            scheduler.queue_program(program[0])
            ui.goto(DashboardControl(ui))

        return MenuControl(ui, program[1], [
            ('Back', lambda: ui.goto(get_root())),
            ('Start', start),
        ])


class ManualRunControl(MenuControl):

    def __init__(self, ui, get_root):
        super().__init__(ui, 'Manual Run', [])
        self.get_root = get_root
        from sprinklerConfiguration import instance as config
        self.duration_by_zone = config.last_manual_run if config else {}
        self.durations = [0, 1, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180]
        self.editing_zone_id = None
        self.default_duration = 30
        self.update_items()

    def get_duration(self, zone_id):
        return self.duration_by_zone[zone_id] if zone_id in self.duration_by_zone else 0

    def get_duration_text(self, zone_id):
        is_editing = zone_id == self.editing_zone_id
        duration = self.get_duration(zone_id)
        if duration == 0 and not is_editing:
            return ''
        has_prev = any(map(lambda d: d < duration, self.durations))
        has_more = any(map(lambda d: d > duration, self.durations))
        units = 's' if duration <= 90 else 'm'
        value = duration if duration <= 90 else duration // 60
        return 'off' if duration == 0 else '{}{}'.format(value, units)

    def on_zone_id_selected(self, zone_id):
        duration = self.get_duration(zone_id)
        if self.editing_zone_id is None:
            self.duration_by_zone[zone_id] = duration if duration > 0 else self.default_duration
            self.editing_zone_id = zone_id
        else:
            if duration > 0:
                self.default_duration = duration
            self.editing_zone_id = None
        self.update_items()

    def on_up(self):
        if self.editing_zone_id is None:
            super().on_up()
            return
        duration = self.get_duration(self.editing_zone_id)
        next_durations = list(filter(lambda d: d < duration, self.durations))
        if len(next_durations) == 0:
            return
        self.duration_by_zone[self.editing_zone_id] = next_durations[-1]
        self.update_items()

    def on_down(self):
        if self.editing_zone_id is None:
            super().on_down()
            return
        duration = self.get_duration(self.editing_zone_id)
        prev_durations = list(filter(lambda d: d > duration, self.durations))
        if len(prev_durations) == 0:
            return
        self.duration_by_zone[self.editing_zone_id] = prev_durations[0]
        self.update_items()

    def start(self):
        from scheduler import instance as scheduler
        from sprinklerConfiguration import instance as config
        if not scheduler or not config:
            return
        config.save_last_manual_run(self.duration_by_zone)
        scheduler.queue_zones(self.duration_by_zone)
        self.ui.goto(DashboardControl(self.ui))

    def update_items(self):
        items = [
            ('Back', lambda: self.ui.goto(self.get_root())),
        ]

        from sprinklerConfiguration import instance as config
        if config:
            def build_zone_item(zone):
                zone_id, zone_name = zone
                zone_name = config.get_zone_name(zone_id)
                duration_text = self.get_duration_text(zone_id)
                editing = zone_id == self.editing_zone_id
                duration = self.get_duration(zone_id)
                adjustable_up = editing and any(
                    map(lambda d: d < duration, self.durations))
                adjustable_down = editing and any(
                    map(lambda d: d > duration, self.durations))
                return (
                    (zone_name, duration_text, adjustable_up, adjustable_down),
                    lambda: self.on_zone_id_selected(zone_id)
                )
            items = items + list(map(build_zone_item, config.get_zones()))

        if any(self.duration_by_zone.values()):
            items.append(('Start', lambda: self.start()))

        if self.index > len(items) - 1:
            self.index = len(items) - 1
        self.items = items
        self.ui.schedule_render()


class WifiStatusControl(UiControl):

    def __init__(self, ui, get_root):
        super().__init__(ui)
        self.get_root = get_root

    def on_select(self):
        self.ui.goto(self.get_root())

    def render(self, oled):
        try:
            import wifiConnect
            status = wifiConnect.getStatus()
            oled.fill(0)
            centered_text(oled, 'WiFi Status', 0)
            oled.text(status['ssid'], 0, 20)
            if status['active']:
                oled.text(status['ip'], 0, 30)
                oled.text('rssi {}'.format(status['rssi']), 0, 40)
            oled.show()
            self.ui.schedule_render(5000)
        except Exception as e:
            oled.fill(0)
            centered_text(oled, 'WiFi Status', 0)
            oled.text('ERROR', 10, 10)
            multi_line_text(oled, repr(e), 20)
            oled.show()
            raise


class ApStatusControl(UiControl):

    def __init__(self, ui, get_root):
        super().__init__(ui)
        self.get_root = get_root

    def on_select(self):
        self.ui.goto(self.get_root())

    def render(self, oled):
        try:
            import network
            sta = network.WLAN(network.AP_IF)
            oled.fill(0)
            centered_text(oled, 'AP Status', 0)
            oled.text(sta.config('essid'), 0, 20)
            oled.text(sta.ifconfig()[0], 0, 30)
            oled.show()
            self.ui.schedule_render(5000)
        except Exception as e:
            oled.fill(0)
            centered_text(oled, 'AP Status', 0)
            oled.text('ERROR', 10, 10)
            multi_line_text(oled, repr(e), 20)
            oled.show()
            raise


class ServerStatusControl(UiControl):

    def __init__(self, ui, get_root):
        super().__init__(ui)
        self.get_root = get_root

    def on_select(self):
        self.ui.goto(self.get_root())

    def render(self, oled):
        try:
            import server
            oled.fill(0)
            centered_text(oled, 'Server Status', 0)
            oled.text('Active: {}'.format(server.is_enabled), 0, 20)
            if server.init_error:
                multi_line_text(oled, 'Error: {}'.format(
                    server.init_error), 20)
            oled.show()
        except Exception as e:
            oled.fill(0)
            centered_text(oled, 'Server Status', 0)
            oled.text('ERROR', 10, 10)
            multi_line_text(oled, repr(e), 20)
            oled.show()
            raise
