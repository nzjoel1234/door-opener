
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


def handlePostTime(httpClient, httpResponse):
    import rtc_time
    body = httpClient.ReadRequestContentAsJSON()
    rtc_time.set_time(body['y'], body['mo'], body['d'],
                      body['h'], body['mi'], body['s'])
    httpResponse.WriteResponseOk()


routeHandlers = [
    ('/status', 'GET', handleGetStatus),
    ('/networks', 'GET', handleGetNetworks),
    ('/network-config', 'POST', handlePostNetworkConfig),
    ('/time', 'POST', handlePostTime),
]


is_enabled = False
init_error = ''


def enable_server():
    global is_enabled, init_error
    try:
        from microWebSrv import MicroWebSrv
        mws = MicroWebSrv(
            routeHandlers=routeHandlers,
            webPath='www')
        mws.Start(threaded=True)
        is_enabled = True
    except Exception as e:
        print('server.enable_server: {}'.format(repr(e)))
        init_error = repr(e)
