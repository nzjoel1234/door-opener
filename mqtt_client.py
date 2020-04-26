import sys
from mqtt_as import MQTTClient, config as default_config
from workScheduler import WorkScheduler


scheduler = WorkScheduler()
client = None
status = 'n/a'


def sub_cb(topic, msg, retained):
    print((topic, msg, retained))
    try:
        t = topic.decode('utf-8')
        m = msg.decode('utf-8')
        print((t, m))
        if t == '123' and m.isdigit():
            print('queuing p{}'.format(m))
            from scheduler import instance
            instance.queue_program(int(m))
    except Exception as e:
        sys.print_exception(e)


def get_config():
    import json
    import wifiConnect
    wifi_config = wifiConnect.get_config()
    config = {}
    config.update(default_config)
    with open('mqtt.json', 'r') as f:
        config.update(json.loads(f.read()))
    config['ssid'] = wifi_config['ssid']
    config['wifi_pw'] = wifi_config['password']
    config['subs_cb'] = sub_cb
    return config


async def try_start():
    global client, status
    try:
        config = get_config()
        client = MQTTClient(config)
        await client.connect()
        await client.subscribe('123', qos=1)
        await client.subscribe('456', qos=1)
        scheduler.schedule_work()
        status = 'Active'
    except Exception as e:
        sys.print_exception(e)
        status = repr(e)


async def do_tasks():
    if not scheduler.work_pending():
        return
    try:
        print('publish')
        await client.publish('test', 'hi from esp32', qos=1)
        print('publish done')
    except Exception as e:
        sys.print_exception(e)
    finally:
        scheduler.schedule_work(20000)
