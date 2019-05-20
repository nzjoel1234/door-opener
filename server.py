
def handleGetStatus(httpClient, httpResponse):
    import wifiConnect
    httpResponse.WriteResponseJSONOk(wifiConnect.getStatus())

def handleGetNetworks(httpClient, httpResponse):
    import wifiConnect
    httpResponse.WriteResponseJSONOk(wifiConnect.scan_networks())

def handlePostNetworkConfig(httpClient, httpResponse):
    import wifiConnect
    body = httpClient.ReadRequestContentAsJSON()
    wifiConnect.save_config(body['ssid'], body['password'])
    httpResponse.WriteResponseJSONOk(wifiConnect.getStatus())

routeHandlers = [
    ('/status', 'GET', handleGetStatus),
    ('/networks', 'GET', handleGetNetworks),
    ('/network-config', 'POST', handlePostNetworkConfig),
]

def enable_server():
    import network
    ap = network.WLAN(network.AP_IF)
    from microWebSrv import MicroWebSrv
    mws = MicroWebSrv(routeHandlers=routeHandlers)
    mws.Start(threaded=True)
    from microDNSSrv import MicroDNSSrv
    my_ip = '192.168.4.1'
    if ap.active():
        my_ip = ap.ifconfig()[0]
    MicroDNSSrv.Create({ '*' : my_ip })
