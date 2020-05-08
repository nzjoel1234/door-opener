import sys
import json
from umqtt.simple import MQTTClient
import wifiConnect
from workScheduler import WorkScheduler


class AwsClient:

    def __init__(self, configurator, zone_scheduler):
        self.configurator = configurator
        self.zone_scheduler = zone_scheduler
        self.client_id = None
        self.client = None
        self.connected = False
        self.reconnect_scheduler = WorkScheduler()
        self.reconnect_scheduler.schedule_work()

    def setup(self):
        try:
            config = get_config()
            self.client_id = config["client_id"]
            server = config["server"]
            del config["client_id"]
            del config["server"]
            self.client = MQTTClient(self.client_id, server, **config)
            self.client.set_callback(
                lambda t, m: self.sub_cb(t.decode('utf-8'), m.decode('utf-8')))
        except Exception as e:
            sys.print_exception(e)

    def get_queue_zones_topic(self):
        return 'sprinkler/{}/queue_zones'.format(self.client_id)

    def get_desired_config_received_topic(self):
        return 'sprinkler/{}/config/desired'.format(self.client_id)

    def get_report_config_topic(self):
        return '$aws/things/{}/shadow/update'.format(self.client_id)

    def sub_cb(self, topic, message):
        try:
            print('MQTT Message: {}'.format((topic, message)))
            if topic == self.get_queue_zones_topic() and message.isdigit():
                duration_by_zone = json.loads(message)
                self.zone_scheduler.queue_zones(duration_by_zone)

            if topic == self.get_desired_config_received_topic():
                shadow = json.loads(message)
                self.configurator.save_config(shadow)
                self.report_config()

        except Exception as e:
            sys.print_exception(e)

    def report_config(self):
        raw_config = self.configurator.read_config()
        self.client.publish(
            bytes(self.get_report_config_topic(), 'UTF-8'),
            bytes(json.dumps({"state": {"reported": raw_config}}), 'UTF-8'))

    def check_connection(self):
        try:
            if not self.client:
                return

            if not wifiConnect.getStatus()['active']:
                self.connected = False
                return

            if self.client.sock is not None:
                try:
                    self.client.ping()
                    self.client.ping()
                except Exception:
                    self.connected = False

            if not self.connected:
                print('aws: connecting')
                self.client.connect()
                print('aws: subscribing')
                self.client.subscribe(
                    bytes(self.get_queue_zones_topic(), 'UTF-8'))
                self.client.subscribe(
                    bytes(self.get_desired_config_received_topic(), 'UTF-8'))
                print('aws: subscribed')
                self.report_config()
                self.connected = True

        except Exception as e:
            self.connected = False
            try:
                self.client.disconnect()
            except Exception:
                pass
            sys.print_exception(e)

    def do_tasks(self):
        if self.reconnect_scheduler.work_pending(10000):
            self.check_connection()
        if self.connected:
            self.client.check_msg()


def get_config():
    config = {}
    with open('mqtt.json', 'r') as f:
        config.update(json.loads(f.read()))
    config['ssl'] = True
    config['keepalive'] = 10000

    ssl_params = {"server_side": False}

    with open("aws/key", "r") as f:
        ssl_params['key'] = f.read()
    with open("aws/cert", "r") as f:
        ssl_params['cert'] = f.read()

    config['ssl_params'] = ssl_params
    return config
