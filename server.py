
mws = None
init_error = ''


def enable_server(configurator, zone_scheduler):

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
        httpResponse.WriteResponseJSONOk([
            {'id': p.id, 'name': p.name}
            for p in configurator.get_programs()
        ])

    def handleGetZones(httpClient, httpResponse):
        httpResponse.WriteResponseJSONOk([
            {'id': z.id, 'name': z.name}
            for z in configurator.get_zones()
        ])

    def handleStart(httpClient, httpResponse):
        body = httpClient.ReadRequestContentAsJSON()
        if body['type'] == 'program':
            zone_scheduler.queue_program(int(body['id']))
        else:
            zone_scheduler.queue_zones({
                i['zone_id']: i['duration'] for i in body['items']
            })
        httpResponse.WriteResponseOk()

    def handleStop(httpClient, httpResponse):
        zone_scheduler.stop_all()
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
