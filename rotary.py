from machine import Pin
from menus import menu_base

menu = None


def goto(new_menu):
    global menu
    menu = new_menu
    menu.render()


def setup():
    goto(menu_base.get_root_menu(goto))

    pin_sw = Pin(26, Pin.IN)
    pin_sw.irq(trigger=Pin.IRQ_FALLING, handler=sw_callback)

    pin_cl = Pin(14, Pin.IN)
    pin_cl.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=cl_callback)

    pin_dt = Pin(27, Pin.IN)
    pin_dt.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=dt_callback)


current_data = False
rotary_history = 0b0000
turn_cw = 0b1100
turn_ccw = 0b1001


def sw_callback(pin):
    global menu
    menu.on_select()


def dt_callback(pin):
    global current_data
    current_data = pin.value() == 1


def cl_callback(pin):
    global rotary_history, turn_cw, turn_ccw, menu
    rotary_history = \
        ((rotary_history & 0b11) << 2) \
        + (0b10 if pin.value() == 1 else 0) \
        + (0b01 if current_data else 0)

    print('cl: ' + bin(rotary_history))

    if rotary_history == turn_cw:
        print('down')
        menu.on_down()
    elif rotary_history == turn_ccw:
        print('up')
        menu.on_up()
