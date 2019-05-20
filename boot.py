import machine
safeModeDetectPin = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)
safeModeIndicatePin = machine.Pin(13, machine.Pin.OUT)
safeModeIndicatePin.off()
if safeModeDetectPin.value() == 0:
    safeModeIndicatePin.on()
    import sys
    sys.exit()

import webrepl
webrepl.start()

import network

def setup_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid='E-SPrinkler', authmode=network.AUTH_WPA_WPA2_PSK, password="esprinkler")

setup_ap()

import server
server.enable_server()

import wifiConnect
wifiConnect.try_connect()
