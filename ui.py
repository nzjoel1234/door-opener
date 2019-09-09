import machine
import ssd1306


def setup():
    global oled
    i2c = machine.I2C(-1, machine.Pin(22), machine.Pin(21))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
    oled.fill(0)
    oled.show()


def menu(items, curr_index):
    num_lines = 5

    first_line = 0
    if curr_index > 2:
        has_more_before = True
        first_line = curr_index - 2

    if len(items) > num_lines and first_line + num_lines > len(items):
        first_line = len(items) - num_lines

    has_more_before = first_line > 0
    has_more_after = first_line + num_lines < len(items)

    global oled
    oled.fill(0)
    # draw arrows to indicate if there are any off-screen items
    if has_more_before:
        for index in range(0, 5):
            oled.hline(63 - index, index + 1, (index + 1) * 2, 1)
    if has_more_after:
        for index in range(0, 5):
            oled.hline(63 - index, 63 - index, (index + 1) * 2, 1)
    for index in range(0, min(num_lines, len(items))):
        text_color = 1
        if first_line + index == curr_index:
            text_color = 0
            oled.fill_rect(0, index * 10 + 7, 128, 10, 1)
        oled.text(items[first_line + index], 0, index * 10 + 8, text_color)
    oled.show()
