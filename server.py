from doorController import DoorController
from doorSensor import DoorSensor

mws = None
init_error = ''


def enable_server(
        doorController: DoorController,
        doorSensor: DoorSensor):

    def handleGetStatus(httpClient, httpResponse):
        try:
            import wifiConnect
            httpResponse.WriteResponseJSONOk(wifiConnect.getStatus())
        except Exception as e:
            sys.print_exception(e)
            raise

    def handleGetNetworks(httpClient, httpResponse):
        try:
            import wifiConnect
            httpResponse.WriteResponseJSONOk(wifiConnect.scan_networks())
        except Exception as e:
            sys.print_exception(e)
            raise

    def handlePostNetworkConfig(httpClient, httpResponse):
        try:
            import wifiConnect
            body = httpClient.ReadRequestContentAsJSON()
            wifiConnect.save_config(body['ssid'], body['password'])
            httpResponse.WriteResponseJSONOk(wifiConnect.getStatus())
        except Exception as e:
            sys.print_exception(e)
            raise

    def handleToggleDoor(httpClient, httpResponse):
        try:
            doorController.toggle_door()
            httpResponse.WriteResponseOk()
        except Exception as e:
            sys.print_exception(e)
            raise

    def handleGetDoorState(httpClient, httpResponse):
        try:
            httpResponse.WriteResponseJSONOk(doorSensor.state)
        except Exception as e:
            sys.print_exception(e)
            raise

    routeHandlers = [
        ('/status', 'GET', handleGetStatus),
        ('/networks', 'GET', handleGetNetworks),
        ('/network-config', 'POST', handlePostNetworkConfig),
        ('/toggle-door', 'POST', handleToggleDoor),
        ('/door-state', 'GET', handleGetDoorState),
    ]

    global mws, init_error
    try:
        from microWebSrv import MicroWebSrv
        mws = MicroWebSrv(
            routeHandlers=routeHandlers,
            webPath='www')
        mws.Start(threaded=True)
    except Exception as e:
        import sys
        sys.print_exception(e)
        init_error = repr(e)
