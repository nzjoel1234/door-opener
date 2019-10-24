from micropython import schedule
import network
import webrepl
from machine import Pin, I2C, Timer
import micropython

micropython.alloc_emergency_exception_buf(100)

shiftR_enable_pin = Pin(26, Pin.OUT)
shiftR_enable_pin.on()

safeModeDetectPin = Pin(23, Pin.IN, Pin.PULL_UP)

safeModeIndicatePin = Pin(2, Pin.OUT)  # onboard blue LED
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


def do_tasks(t):

    from ui import instance as ui_manager
    if ui_manager:
        ui_manager.do_tasks()

    from scheduler import instance as schedule_manager
    if schedule_manager:
        schedule_manager.do_tasks()


def setup():
    loadingControl = None
    try:
        i2c = I2C(-1, Pin(22), Pin(21))

        def on_timer(t): return schedule(do_tasks, 0)
        Timer(-1).init(period=100, mode=Timer.PERIODIC,
                       callback=on_timer)

        import ui
        ui_man = ui.setup(i2c)
        loadingControl = ui.LoadingControl(ui_man)
        ui_man.goto(loadingControl)

        loadingControl.set_status("rtc")
        import rtc_time
        rtc_time.setup(i2c)

        loadingControl.set_status("scheduler")
        from sprinklerConfiguration import setup as SetupConfig
        from scheduler import setup as setupScheduler
        from shiftR import ShiftR
        sprinklerConfiguration = SetupConfig()
        shiftR = ShiftR(shiftR_enable_pin, Pin(14, Pin.OUT),
                        Pin(13, Pin.OUT), Pin(27, Pin.OUT), sprinklerConfiguration.get_zone_num())
        shiftR.setup()
        setupScheduler(SetupConfig(), shiftR)

        loadingControl.set_status("rotary")
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
        if loadingControl:
            loadingControl.set_detail(repr(e))
        raise


try:
    setup()
except Exception as e:
    print('Initialisation error: {}'.format(repr(e)))
    raise
