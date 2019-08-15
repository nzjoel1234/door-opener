import machine
import ssd1306


oled = None


def setup():
    global oled
    i2c = machine.I2C(-1, machine.Pin(22), machine.Pin(21))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
    return oled


def render_menu(items, curr_index, going_up=false):
    global oled
    oled.fill(0)
    first_line = 0
    max_first_line = 3
    if going_up:
        max_first_line = 2
    if curr_index > max_first_line:
        first_line = curr_index - max_first_line
    if first_line + 6 > len(items):
        first_line = len(items) - 6
    for index in range(0, min(6, len(items))):
        text_color = 1
        if index + first_line == curr_index:
            text_color = 0
            oled.fill_rect(0, index * 10, 128, 10, 1)
        oled.text(items[first_line + index], 0, index * 10 + 1, text_color)
    oled.show()
