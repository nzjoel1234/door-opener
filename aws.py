
def get_date_time():
    import ntptime
    ntptime.settime()
    import utime
    time_tuple = utime.localtime()
    datestamp = "{0}{1:02d}{2:02d}".format(time_tuple[0], time_tuple[1], time_tuple[2])
    time_now_utc = "{0:02d}{1:02d}{2:02d}".format(time_tuple[3], time_tuple[4], time_tuple[5])
    return (datestamp + "T" + time_now_utc + "Z")

def makeShadowRequest(method = 'GET', body = '', contentType = 'application/json'):
    import awsiot_sign
    import json
    config = {}
    with open('aws.json', 'r') as f:
        config = json.loads(f.read())

    signed = awsiot_sign.request_gen(\
        config['end_point_prefix'], \
        config['thing_id'], \
        config['access_key'], \
        config['secret_access_key'], \
        get_date_time(), \
        region=config['region'], \
        method=method, \
        body=body)

    from microWebCli import MicroWebCli
    cli = MicroWebCli(auth = AuthIgnore())
    cli.Headers = signed['headers']
    cli.Method = method
    cli.URL = 'https://' + signed['host'] + signed['uri']
    if body:
        cli.OpenRequest(body, contentType)
    else:
        cli.OpenRequest()
    return cli.GetResponse()

def getShadow():
    res = makeShadowRequest()
    if not res.IsSuccess():
        return None
    with open('shadowResponse.json', 'wb+') as f:
        while not res.IsClosed():
            b = res.ReadContent(1)
            if b is None:
                break
            f.write(str(b, 'utf-8'))
    import json
    shadowResponse = None
    with open('shadowResponse.json', 'r') as f:
        shadowResponse = json.load(f)
    return shadowResponse

def updateShadow():
    shadowResponse = getShadow()
    if shadowResponse is None:
        return False
    import json
    if 'state' not in shadowResponse or \
       'delta' not in shadowResponse['state']:
        return None
    if 'desired' not in shadowResponse['state']:
        return False
    activeShadow = shadowResponse['state']['desired']
    with open('activeShadow.json', 'wb+') as f:
        f.write(json.dumps(activeShadow))
    body = json.dumps({ 'state': { 'reported': activeShadow } })
    response = makeShadowRequest('POST', body)
    success = response.IsSuccess()
    response.Close()
    return success

def getActiveShadow():
    try:
        import json
        with open('activeShadow.json', 'r') as f:
            return json.load(f)
    except:
        return None


class AuthIgnore:
    def Apply(self, microWebCli):
        pass
