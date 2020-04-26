from micropython import schedule
from machine import Pin
import utime
from ui import UiManager

turn_cw = 0b1100
turn_ccw = 0b1001


class Rotary:

    def __init__(self, ui: UiManager):
        self.ui = ui
        self.current_data = False
        self.rotary_history = 0b0000
        self.last_click_t = None
        self.on_down = lambda x: ui.on_down()
        self.on_up = lambda x: ui.on_up()
        self.on_select = lambda x: ui.on_select()

    def setup(self, pin_sw, pin_cl, pin_dt):
        pin_sw.irq(trigger=Pin.IRQ_FALLING, handler=self.sw_callback)
        pin_cl.irq(trigger=Pin.IRQ_RISING |
                   Pin.IRQ_FALLING, handler=self.cl_callback)
        pin_dt.irq(trigger=Pin.IRQ_RISING |
                   Pin.IRQ_FALLING, handler=self.dt_callback)

    def sw_callback(self, pin):
        schedule(self.on_select, 0)

    def dt_callback(self, pin):
        self.current_data = pin.value() == 1

    def cl_callback(self, pin):
        self.rotary_history = \
            ((self.rotary_history & 0b11) << 2) \
            + (0b10 if pin.value() == 1 else 0) \
            + (0b01 if self.current_data else 0)

        if self.rotary_history == turn_cw:
            schedule(self.on_down, 0)
        elif self.rotary_history == turn_ccw:
            schedule(self.on_up, 0)
