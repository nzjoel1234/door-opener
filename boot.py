import sys
import network
import webrepl
import machine
import micropython
import _thread
import utime
import uasyncio as asyncio

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

def mem(label = 'mem'):
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

mqtt_client = None

def setup():
    loadingControl = None
    try:
        i2c = machine.I2C(-1, machine.Pin(22), machine.Pin(21))

        import ui
        ui_man = ui.setup(i2c)
        loadingControl = ui.LoadingControl(ui_man)
        ui_man.goto(loadingControl)

        loadingControl.set_status("server")
        import server
        # For some reason starting server on main thread makes first server request VERY slow (>20secs)
        server.enable_server()

        loadingControl.set_status("rtc")
        import rtc_time
        rtc_time.setup(i2c)

        loadingControl.set_status("config")
        from sprinklerConfiguration import setup as SetupConfig
        sprinklerConfiguration = SetupConfig()

        loadingControl.set_status("shiftr")
        from shiftR import ShiftR
        shiftR = ShiftR(shiftR_enable_pin,
                        machine.Pin(14, machine.Pin.OUT),
                        machine.Pin(13, machine.Pin.OUT),
                        machine.Pin(27, machine.Pin.OUT),
                        sprinklerConfiguration.get_zone_num())
        shiftR.setup()

        loadingControl.set_status("scheduler")
        from scheduler import setup as setupScheduler
        setupScheduler(sprinklerConfiguration, shiftR)

        loadingControl.set_status("rotary")
        from rotary import Rotary
        rotary = Rotary(ui_man)
        rotary.setup(rotary_sw_pin, rotary_cl_pin, rotary_dt_pin)

        loadingControl.set_status("ap")
        setup_ap()

        # loadingControl.set_status("wifi")
        # import wifiConnect
        # wifiConnect.try_connect()

        loadingControl.set_status("display")
        ui_man.goto(ui.DashboardControl(ui_man))

    except Exception as e:
        if loadingControl:
            loadingControl.set_detail(repr(e))
        sys.print_exception(e)
        raise


async def main():
    while True:
        try:
            from ui import instance as ui_manager
            if ui_manager:
                ui_manager.do_tasks()

            from scheduler import instance as schedule_manager
            if schedule_manager:
                schedule_manager.do_tasks()
                
            import mqtt_client as mqtt
            await mqtt.do_tasks()

        except Exception as e:
            sys.print_exception(e)
        await asyncio.sleep_ms(100)

async def setup_mqtt():
    import mqtt_client
    await mqtt_client.try_start()

_thread.start_new_thread(setup, ())

loop = asyncio.get_event_loop()
loop.create_task(setup_mqtt())
loop.run_until_complete(main())
