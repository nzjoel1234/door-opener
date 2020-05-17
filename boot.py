import ssd1306
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

rotary_sw_pin = machine.Pin(32, machine.Pin.IN)
rotary_cl_pin = machine.Pin(25, machine.Pin.IN)
rotary_dt_pin = machine.Pin(33, machine.Pin.IN)

safeModeDetectPin = machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_UP)

safeModeIndicatePin = machine.Pin(2, machine.Pin.OUT)  # onboard blue LED
safeModeIndicatePin.off()

if rotary_sw_pin.value() == 1 or safeModeDetectPin.value() == 0:
    safeModeIndicatePin.on()
    print('*****')
    print('Booted into SAFE MODE')
    print('*****')
    sys.exit()


def mem(label='mem'):
    print('--------------')
    print(label)
    import gc
    gc.collect()
    micropython.mem_info()


webrepl.start(password='admin')


def setup_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='E-SPrinkler',
              authmode=network.AUTH_WPA_WPA2_PSK,
              password="esprinkler")


aws_client = None
zone_scheduler = None
ui_manager = None
rtc_time = None


def setup():
    loadingControl = None
    try:
        i2c = machine.I2C(-1, machine.Pin(22), machine.Pin(21))
        oled = ssd1306.SSD1306_I2C(128, 64, i2c)

        global ui_manager, zone_scheduler, aws_client, rtc_time

        import ui
        ui_manager = ui.UiManager(oled)
        loadingControl = ui.LoadingControl(ui_manager)
        ui_manager.goto(loadingControl)

        loadingControl.set_status("config")
        from sprinklerConfiguration import SprinklerConfiguration
        configurator = SprinklerConfiguration()
        configurator.load_config()
        ui_manager.configurator = configurator

        loadingControl.set_status("rtc")
        from rtcTime import RtcTime
        rtc_time = RtcTime()
        rtc_time.setup(i2c)
        ui_manager.rtc_time = rtc_time

        loadingControl.set_status("shiftr")
        from shiftR import ShiftR
        shiftR = ShiftR(shiftR_enable_pin,
                        machine.Pin(14, machine.Pin.OUT),
                        machine.Pin(13, machine.Pin.OUT),
                        machine.Pin(27, machine.Pin.OUT),
                        configurator.get_zone_num())
        shiftR.setup()

        loadingControl.set_status("scheduler")
        from zoneScheduler import ZoneScheduler
        zone_scheduler = ZoneScheduler(configurator, shiftR)
        zone_scheduler.queue_changed_event.add_handler(
            lambda q: print(q.serialise()))
        ui_manager.zone_scheduler = zone_scheduler

        loadingControl.set_status("server")
        import server
        server.enable_server(configurator, zone_scheduler)

        loadingControl.set_status("rotary")
        from rotary import Rotary
        rotary = Rotary(ui_manager)
        rotary.setup(rotary_sw_pin, rotary_cl_pin, rotary_dt_pin)

        loadingControl.set_status("ap")
        setup_ap()

        loadingControl.set_status("wifi")
        import wifiConnect
        wifiConnect.try_connect()

        loadingControl.set_status("aws")
        from awsClient import AwsClient
        temp_aws_client = AwsClient(configurator, zone_scheduler)
        temp_aws_client.setup()
        aws_client = temp_aws_client

        loadingControl.set_status("display")
        ui_manager.goto(ui.DashboardControl(ui_manager))

    except Exception as e:
        if loadingControl:
            loadingControl.set_detail(repr(e))
        sys.print_exception(e)
        raise


def ui_loop():
    while True:
        try:
            if ui_manager:
                ui_manager.do_tasks()

        except Exception as e:
            sys.print_exception(e)
        utime.sleep_ms(100)


def background_loop():
    while True:
        try:
            if rtc_time:
                rtc_time.do_tasks()

            if zone_scheduler:
                zone_scheduler.do_tasks()

            if aws_client:
                aws_client.do_tasks()

        except Exception as e:
            sys.print_exception(e)
        utime.sleep_ms(100)


_thread.start_new_thread(setup, ())
_thread.start_new_thread(ui_loop, ())
_thread.start_new_thread(background_loop, ())
