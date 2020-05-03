
import network
import json


def save_config(ssid, password):
    with open('network.json', 'w+') as f:
        f.write(json.dumps({'ssid': ssid, 'password': password}))
    try_connect(forceReconnect=True)


def get_config():
    try:
        with open('network.json', 'r') as f:
            return json.loads(f.read())
    except:
        return None


def scan_networks():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    return list(map(lambda n: {'ssid': n[0], 'rssi': n[3]}, sta.scan()))


def getStatus():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        config = get_config()
        return {
            'active': False,
            'ssid': config['ssid'] if config is not None else 'n/a',
        }
    return {
        'active': True,
        'ssid': sta.config('essid'),
        'ip': sta.ifconfig()[0],
        'rssi': sta.status('rssi')
    }


def try_connect(forceReconnect=False):
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    config = get_config()
    if (config is None) or ('ssid' not in config) or (config['ssid'] is None):
        return
    if forceReconnect:
        sta_if.disconnect()
    if sta_if.config('essid') == config['ssid'] and sta_if.isconnected():
        return
    sta_if.connect(config['ssid'], config['password'])
