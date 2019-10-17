from machine import Pin
import utime

turn_cw = 0b1100
turn_ccw = 0b1001


class Rotary:

    def __init__(self, ui):
        self.ui = ui
        self.current_data = False
        self.rotary_history = 0b0000
        self.last_click_t = None

    def setup(self):
        pin_sw = Pin(26, Pin.IN)
        pin_sw.irq(trigger=Pin.IRQ_FALLING, handler=self.sw_callback)

        pin_cl = Pin(14, Pin.IN)
        pin_cl.irq(trigger=Pin.IRQ_RISING |
                   Pin.IRQ_FALLING, handler=self.cl_callback)

        pin_dt = Pin(27, Pin.IN)
        pin_dt.irq(trigger=Pin.IRQ_RISING |
                   Pin.IRQ_FALLING, handler=self.dt_callback)

    def sw_callback(self, pin):
        if self.last_click_t is not None and utime.ticks_diff(utime.ticks_ms(), self.last_click_t) < 200:
            return
        self.last_click_t = utime.ticks_ms()
        self.ui.on_select()

    def dt_callback(self, pin):
        self.current_data = pin.value() == 1

    def cl_callback(self, pin):
        self.rotary_history = \
            ((self.rotary_history & 0b11) << 2) \
            + (0b10 if pin.value() == 1 else 0) \
            + (0b01 if self.current_data else 0)

        if self.rotary_history == turn_cw:
            self.ui.on_down()
        elif self.rotary_history == turn_ccw:
            self.ui.on_up()
