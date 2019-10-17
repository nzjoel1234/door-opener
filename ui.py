import machine
import utime
import ssd1306
import _thread


def setup(i2c):
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
    ui_manager = UiManager()
    ui_tim = machine.Timer(-1)
    ui_tim.init(period=100, mode=machine.Timer.PERIODIC,
                callback=lambda t: ui_manager.render(oled))
    return ui_manager


def draw_prev_arrow(oled):
    for index in range(0, 5):
        oled.hline(63 - index, index + 1, (index + 1) * 2, 1)


def draw_next_arrow(oled):
    for index in range(0, 5):
        oled.hline(63 - index, 63 - index, (index + 1) * 2, 1)


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


def draw_menu(oled, items, curr_index):
    num_lines = 5
    first_line = 0

    if len(items) > num_lines:
        if curr_index > 2:
            first_line = curr_index - 2
        if first_line + num_lines > len(items):
            first_line = len(items) - num_lines

    oled.fill(0)

    # draw arrows to indicate if there are any off-screen items
    has_more_before = first_line > 0
    if has_more_before:
        draw_prev_arrow(oled)

    has_more_after = first_line + num_lines < len(items)
    if has_more_after:
        draw_next_arrow(oled)

    for index in range(0, min(num_lines, len(items))):
        item_index = first_line + index
        text_color = 1
        if item_index == curr_index:
            text_color = 0
            oled.fill_rect(0, index * 10 + 7, 128, 10, 1)
        oled.text(items[item_index], 0, index * 10 + 8, text_color)
    oled.show()


class UiManager:

    def __init__(self):
        self.current_control = None
        self.render_scheduled = False
        self.goto(LoadingControl(self))

    def goto(self, new_control):
        self.current_control = new_control
        self.schedule_render()

    def schedule_render(self, millis=0):
        self.next_render_millis = utime.ticks_add(utime.ticks_ms(), millis)
        self.render_scheduled = True

    def render(self, oled):
        try:
            if not self.render_scheduled:
                return
            diff = utime.ticks_diff(utime.ticks_ms(), self.next_render_millis)
            if diff >= 0:
                self.render_scheduled = False
                self.current_control.render(oled)
        except Exception as e:
            print('render error: {}'.format(repr(e)))
            self.schedule_render(2000)  # Try render again in 2 seconds

    def on_up(self):
        self.current_control.on_up()

    def on_down(self):
        self.current_control.on_down()

    def on_select(self):
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
        self.status = ""
        self.detail = ""

    def set_status(self, status):
        self.status = status
        self.detail = ""
        self.ui.schedule_render()

    def set_detail(self, detail):
        self.detail = detail
        self.ui.schedule_render()

    def render(self, oled):
        y, mo, d, h, mi, s, *rest = utime.localtime()
        oled.fill(0)
        centered_text(oled, "Loading...", 0)
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
        self.ui.goto(MenuControl.get_root_menu(self.ui))

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
            #f = oled.fill_rect if bar['fill'] else oled.rect
            # x, y, w, h, c
            y = max_bar_height - bar['h']
            oled.fill_rect(bar['x'], y, bar_width, bar['h'], 1)

        text_right(oled, '--' if rssi is None else str(rssi),
                   first_bar_x - 2, 0)

        y, mo, d, h, mi, s, wd, yd = utime.localtime()

        week_day = week_day_labels[wd]
        oled.text("{:02d}:{:02d}".format(h, mi), 0, 0)

        centered_text(oled, "{} {:02d}-{:02d}-{:02d}".format(
            week_day, d, mo, y % 100), 20)
        oled.show()
        self.ui.schedule_render(min(10000, (60 - s) * 1000 + 100))


class MenuControl(UiControl):

    def __init__(self, ui, items):
        super().__init__(ui)
        self.index = 0
        self.items = items

    def render(self, oled):
        draw_menu(oled,
                  list(map(lambda item: item[0], self.items)),
                  self.index)

    def on_down(self):
        if self.index < len(self.items) - 1:
            self.index += 1
            self.ui.schedule_render()

    def on_up(self):
        if self.index > 0:
            self.index -= 1
            self.ui.schedule_render()

    def on_select(self):
        self.ui.goto(self.items[self.index][1]())

    @staticmethod
    def get_root_menu(ui):
        return MenuControl(ui, [
            ('Back', lambda: DashboardControl(ui)),
            ('Info', lambda: MenuControl.get_info_menu(ui)),
        ])

    @staticmethod
    def get_info_menu(ui, get_root=None):
        def get_this(): return MenuControl.get_info_menu(ui, get_root)
        return MenuControl(ui, [
            ('Back', lambda: MenuControl.get_root_menu(
                ui) if get_root is None else get_root()),
            ('WiFi Status', lambda: WifiStatusControl(ui, get_root=get_this)),
            ('AP Status', lambda: ApStatusControl(ui, get_root=get_this)),
            ('Server Status', lambda: ServerStatusControl(ui, get_root=get_this)),
        ])


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
            oled.text('WiFi Status', 0, 0)
            oled.text(status['ssid'], 0, 20)
            if status['active']:
                oled.text(status['ip'], 0, 30)
                oled.text("rssi {}".format(status['rssi']), 0, 40)
            oled.show()
            self.ui.schedule_render(5000)
        except Exception as e:
            oled.fill(0)
            oled.text("WiFi Status", 0, 0)
            oled.text("ERROR", 10, 10)
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
            oled.text("AP Status", 0, 0)
            oled.text(sta.config('essid'), 0, 20)
            oled.text(sta.ifconfig()[0], 0, 30)
            oled.show()
            self.ui.schedule_render(5000)
        except Exception as e:
            oled.fill(0)
            oled.text("AP Status", 0, 0)
            oled.text("ERROR", 10, 10)
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
            oled.text("Server Status", 0, 0)
            oled.text("Active: {}".format(server.is_enabled), 0, 20)
            if server.init_error:
                multi_line_text(oled, "Error: {}".format(
                    server.init_error), 20)
            oled.show()
        except Exception as e:
            oled.fill(0)
            oled.text("Server Status", 0, 0)
            oled.text("ERROR", 10, 10)
            multi_line_text(oled, repr(e), 20)
            oled.show()
            raise
