
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

    access_key = 'AKIAYBXV5UBP7XHO23UM'
    secret_access_key = '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'
    end_point_prefix = 'a3ifeswmcxw4rt-ats'
    thing_id = 'sprinkler'
    region = 'us-west-2'

    signed = awsiot_sign.request_gen(\
        end_point_prefix, thing_id, access_key, secret_access_key, get_date_time(), region=region)

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
