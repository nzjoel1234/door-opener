import sys
import network
import webrepl
import machine
import micropython
import _thread
import utime

micropython.alloc_emergency_exception_buf(100)

shiftR_enable_pin = machine.Pin(26, machine.Pin.OUT)
shiftR_enable_pin.on()

safeModeDetectPin = machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_UP)

safeModeIndicatePin = machine.Pin(2, machine.Pin.OUT)  # onboard blue LED
safeModeIndicatePin.off()

if safeModeDetectPin.value() == 0:
    safeModeIndicatePin.on()
    print('*****')
    print('Booted into SAFE MODE')
    print('*****')
    sys.exit()

webrepl.start(password='admin')


def setup_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='E-SPrinkler',
              authmode=network.AUTH_WPA_WPA2_PSK,
              password="esprinkler")


def setup():
    loadingControl = None
    try:
        i2c = machine.I2C(-1, machine.Pin(22), machine.Pin(21))

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
        shiftR = ShiftR(shiftR_enable_pin,
                        machine.Pin(14, machine.Pin.OUT),
                        machine.Pin(13, machine.Pin.OUT),
                        machine.Pin(27, machine.Pin.OUT),
                        sprinklerConfiguration.get_zone_num())
        shiftR.setup()
        setupScheduler(SetupConfig(), shiftR)

        loadingControl.set_status("rotary")
        from rotary import Rotary
        rotary = Rotary(ui_man)
        rotary.setup()

        loadingControl.set_status("ap")
        setup_ap()

        loadingControl.set_status("server")
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
        sys.print_exception(e)
        raise


def do_tasks():
    while True:
        try:
            from ui import instance as ui_manager
            if ui_manager:
                ui_manager.do_tasks()

            from scheduler import instance as schedule_manager
            if schedule_manager:
                schedule_manager.do_tasks()
        except Exception as e:
            sys.print_exception(e)
        utime.sleep_ms(100)


_thread.start_new_thread(setup, ())
_thread.start_new_thread(do_tasks, ())
