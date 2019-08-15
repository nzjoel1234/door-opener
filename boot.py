import wifiConnect
import server
import network
import webrepl
import machine
safeModeDetectPin = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)
safeModeIndicatePin = machine.Pin(13, machine.Pin.OUT)
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


setup_ap()

server.enable_server()

wifiConnect.try_connect()
