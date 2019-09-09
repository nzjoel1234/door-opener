import network
import webrepl
from machine import Pin
import micropython

micropython.alloc_emergency_exception_buf(100)

safeModeDetectPin = Pin(12, Pin.IN, Pin.PULL_UP)
safeModeIndicatePin = Pin(13, Pin.OUT)
safeModeIndicatePin.off()
if safeModeDetectPin.value() == 0:
    safeModeIndicatePin.on()
    import sys
    sys.exit()

webrepl.start()


def setup_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='E-SPrinkler',
              authmode=network.AUTH_WPA_WPA2_PSK, password="esprinkler")


def setup():
    setup_ap()
    import wifiConnect
    wifiConnect.try_connect()
    import server
    server.enable_server()
    import ui
    ui.setup()
    import rotary
    rotary.setup()


try:
    setup()
except Exception as e:
    print(e)
