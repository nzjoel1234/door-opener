
def handleGetStatus(httpClient, httpResponse):
    import network
    sta = network.WLAN(network.STA_IF)
    if not sta.isconnected():
        httpResponse.WriteResponseJSONOk({ 'active': False })
        return
    httpResponse.WriteResponseJSONOk({
        'active': True,
        'name': sta.config('essid'),
        'ip': sta.ifconfig()[0]
    })

def handleGetNetworks(httpClient, httpResponse):
    import network
    sta = network.WLAN(network.STA_IF)
    networks = list(map(lambda n: { 'name': n[0], 'rssi': n[3] }, sta.scan()))
    httpResponse.WriteResponseJSONOk(networks)

routeHandlers = [
    ('/status', 'GET', handleGetStatus),
    ('/networks', 'GET', handleGetNetworks),
]

def enable_server():
    from microWebSrv import MicroWebSrv
    mws = MicroWebSrv(routeHandlers=routeHandlers)
    mws.Start(threaded=True)
