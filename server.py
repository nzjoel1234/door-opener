
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


def handleGetPrograms(httpClient, httpResponse):
    from sprinklerConfiguration import SprinklerConfiguration
    config = SprinklerConfiguration()
    if config is None:
        httpResponse.WriteResponseInternalServerError()
        return
    httpResponse.WriteResponseJSONOk([
        {'id': id, 'name': config.get_program_name(id)}
        for id in config.get_program_ids()
    ])


def handleGetZones(httpClient, httpResponse):
    from sprinklerConfiguration import instance as config
    if config is None:
        httpResponse.WriteResponseInternalServerError()
        return
    httpResponse.WriteResponseJSONOk([
        {'id': id, 'name': config.get_zone_name(id)}
        for id in config.get_zone_ids()
    ])


def handleStart(httpClient, httpResponse):
    from scheduler import instance as scheduler
    if scheduler is None:
        httpResponse.WriteResponseInternalServerError()
        return
    body = httpClient.ReadRequestContentAsJSON()
    if body['type'] == 'program':
        scheduler.queue_program(int(body['id']))
    else:
        scheduler.queue_zones({
            i['zone_id']: i['duration'] for i in body['items']
        })
    httpResponse.WriteResponseOk()


def handleStop(httpClient, httpResponse):
    from scheduler import instance as scheduler
    if scheduler is None:
        httpResponse.WriteResponseInternalServerError()
        return
    scheduler.stop_all()
    httpResponse.WriteResponseOk()


routeHandlers = [
    ('/status', 'GET', handleGetStatus),
    ('/networks', 'GET', handleGetNetworks),
    ('/network-config', 'POST', handlePostNetworkConfig),
    ('/time', 'POST', handlePostTime),
    ('/programs', 'GET', handleGetPrograms),
    ('/zones', 'GET', handleGetZones),
    ('/start', 'POST', handleStart),
    ('/stop', 'POST', handleStop),
]


mws = None
init_error = ''


def enable_server():
    global mws, init_error
    try:
        from microWebSrv import MicroWebSrv
        mws = MicroWebSrv(
            routeHandlers=routeHandlers,
            webPath='www')
        mws.Start(threaded=True)
        is_enabled = True
    except Exception as e:
        import sys
        sys.print_exception(e)
        init_error = repr(e)
