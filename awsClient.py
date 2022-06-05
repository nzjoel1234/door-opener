import sys
import json
from doorSensor import DoorSensor, DoorStates
from umqtt.simple import MQTTClient
import networkHelper
from workScheduler import WorkScheduler
from doorController import DoorController
from networkTime import NetworkTime
import machine


class AwsClient:

    def __init__(self, door_controller: DoorController, door_sensor: DoorSensor, network_time: NetworkTime):
        self.door_controller = door_controller
        self.door_sensor = door_sensor
        self.network_time = network_time
        self.door_sensor.state_changed_event.add_handler(self.publish_state)
        self.client_id = None
        self.client = None
        self.connected = False
        self.reconnect_scheduler = WorkScheduler(True)

    def __del__(self):
        self.door_sensor.state_changed_event.remove_handler(
            self.publish_state)

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

    def get_toggle_request_topic(self):
        return 'door-opener/{}/toggle/request'.format(self.client_id)

    def get_toggle_response_topic(self):
        return 'door-opener/{}/toggle/response'.format(self.client_id)

    def get_state_request_topic(self):
        return 'door-opener/{}/state/request'.format(self.client_id)

    def get_state_update_topic(self):
        return 'door-opener/{}/state/update'.format(self.client_id)

    def get_reset_topic(self):
        return 'door-opener/{}/reset'.format(self.client_id)

    def sub_cb(self, topic, message):
        try:
            print('MQTT Message: {}'.format((topic, message)))

            if topic == self.get_toggle_request_topic():
                self.door_controller.toggle_door()
                self.publish(self.get_toggle_response_topic(), '')

            if topic == self.get_state_request_topic():
                self.publish_state()

            if topic == self.get_reset_topic():
                machine.reset()

        except Exception as e:
            sys.print_exception(e)

    def publish(self, topic, message):
        self.client.publish(bytes(topic, 'UTF-8'),
                            bytes(message, 'UTF-8'))

    def subscribe(self, topic):
        self.client.subscribe(bytes(topic, 'UTF-8'))

    def publish_state(self, state: DoorStates = None):
        state = state or self.door_sensor.state
        self.publish(self.get_state_update_topic(), str(state))

    def check_connection(self):
        try:
            if not self.client:
                return

            if (not self.network_time.ntp_loaded) or (not networkHelper.isWiFiActive()):
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
                self.subscribe(self.get_toggle_request_topic())
                self.subscribe(self.get_state_request_topic())
                self.subscribe(self.get_reset_topic())
                print('aws: subscribed')
                print('aws: publishing initial state')
                self.publish_state()
                print('aws: published initial state')
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
