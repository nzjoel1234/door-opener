
def get_date_time():
    import ntptime
    ntptime.settime()
    import utime
    time_tuple = utime.localtime()
    datestamp = "{0}{1:02d}{2:02d}".format(time_tuple[0], time_tuple[1], time_tuple[2])
    time_now_utc = "{0:02d}{1:02d}{2:02d}".format(time_tuple[3], time_tuple[4], time_tuple[5])
    return (datestamp + "T" + time_now_utc + "Z")

def getShadow(size=None):
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
        region=config['region'])

    from microWebCli import MicroWebCli
    cli = MicroWebCli(auth = AuthIgnore())
    cli.Headers = signed['headers']
    cli.Method = 'GET'
    cli.URL = 'https://' + signed['host'] + signed['uri']
    cli.OpenRequest()
    res = cli.GetResponse()
    if not res.IsSuccess():
        return False
    with open('shadow.json', 'wb+') as f:
        while not res.IsClosed():
            b = res.ReadContent(1)
            if b is None:
                break
            f.write(str(b, 'utf-8'))
    return True

class AuthIgnore:
    def Apply(self, microWebCli):
        pass
