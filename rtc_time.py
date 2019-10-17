from ds3231_port import DS3231

ds3231 = None


def setup(i2c):
    global ds3231
    ds3231 = DS3231(i2c)
    ds3231.get_time(set_rtc=True)


def set_time(y, mo, d, h, mi, s):
    import machine
    rtc = machine.RTC()
    rtc.datetime((y, mo, d, 0, h, mi, s, 0))
    ds3231.save_time()
