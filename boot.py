import network
import webrepl
from machine import Pin, I2C, Timer
import micropython

micropython.alloc_emergency_exception_buf(100)

safeModeDetectPin = Pin(12, Pin.IN, Pin.PULL_UP)
safeModeIndicatePin = Pin(13, Pin.OUT)
safeModeIndicatePin.off()
if safeModeDetectPin.value() == 0:
    safeModeIndicatePin.on()
    import sys
    sys.exit()

webrepl.start(password='admin')


def setup_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='E-SPrinkler',
              authmode=network.AUTH_WPA_WPA2_PSK,
              password="esprinkler")


def setup():
    i2c = I2C(-1, Pin(22), Pin(21))
    import ui
    ui_man = ui.setup(i2c)
    loadingControl = ui.LoadingControl(ui_man)
    ui_man.goto(loadingControl)

    try:

        loadingControl.set_status("rtc")
        import rtc_time
        rtc_time.setup(i2c)

        loadingControl.set_status("input")
        from rotary import Rotary
        rotary = Rotary(ui_man)
        rotary.setup()

        loadingControl.set_status("ap")
        setup_ap()

        loadingControl.set_status("server")
        import _thread
        import server
        # For some reason starting server on main thread makes first server request VERY slow (>20secs)
        _thread.start_new_thread(server.enable_server, ())

        loadingControl.set_status("wifi")
        import wifiConnect
        wifiConnect.try_connect()

        loadingControl.set_status("display")
        ui_man.goto(ui.DashboardControl(ui_man))

    except Exception as e:
        loadingControl.set_detail(repr(e))
        raise


try:
    setup()
except Exception as e:
    print('Initialisation error: {}'.format(repr(e)))
