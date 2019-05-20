
def save_config(ssid, password):
    import json
    with open('network.json', 'w+') as f:
        f.write(json.dumps({ 'ssid': ssid, 'password': password }))
    try_connect(forceReconnect=True)

def get_config():
    import json
    with open('network.json', 'r') as f:
        return json.loads(f.read())

def scan_networks():
    import network
    sta = network.WLAN(network.STA_IF)
    return list(map(lambda n: { 'ssid': n[0], 'rssi': n[3] }, sta.scan()))

def getStatus():
    import network
    sta = network.WLAN(network.STA_IF)
    if not sta.isconnected():
        config = get_config()
        return {
            'active': False,
            'ssid': config['ssid'],
        }
    return {
        'active': True,
        'ssid': sta.config('essid'),
        'ip': sta.ifconfig()[0]
    }

def try_connect(forceReconnect=False):
    try:
        import json
        config = get_config()
        if not ('ssid' in config and config['ssid']):
            return
        import network
        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(True)
        if forceReconnect:
            sta_if.disconnect()
        if sta_if.config('essid') == config['ssid'] and sta_if.isconnected():
            return
        sta_if.connect(config['ssid'], config['password'])
        while sta_if.status() == network.STAT_CONNECTING:
            pass
        if sta_if.isconnected():
            print('network config:', sta_if.ifconfig())
        else:
            print('Failed to connect. Status: ' + sta_if.status())
    except Exception as e:
        print(str(e))
