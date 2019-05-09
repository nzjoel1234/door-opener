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

def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('<SSID>', '<PASS>')
        while not sta_if.isconnected():
            pass
    print('network config:', sta_if.ifconfig())

do_connect()
