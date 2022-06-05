import sys
import webrepl
import machine
import micropython
import _thread
import utime

micropython.alloc_emergency_exception_buf(100)

door_relay_pin = machine.Pin(12, machine.Pin.OUT)
door_relay_pin.off()

door_hall_sense_pin = machine.Pin(19, machine.Pin.IN, machine.Pin.PULL_UP)
door_left_encoder_pin = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_UP)
door_right_encoder_pin = machine.Pin(21, machine.Pin.IN, machine.Pin.PULL_UP)

safeModeDetectPin = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)

safeModeIndicatePin = machine.Pin(2, machine.Pin.OUT)  # onboard blue LED
safeModeIndicatePin.off()

if safeModeDetectPin.value() == 0:
    safeModeIndicatePin.on()
    print('*****')
    print('Booted into SAFE MODE')
    print('*****')
    sys.exit()


webrepl.start(password='admin')


aws_client = None
network_time = None
door_controller = None
door_sensor = None


def setup():
    loadingControl = None
    try:

        global aws_client, network_time, door_controller, door_sensor

        print('BOOT: DoorController')
        from doorController import DoorController
        door_controller = DoorController(door_relay_pin)

        print('BOOT: DoorSensor')
        from doorSensor import DoorSensor
        door_sensor_temp = DoorSensor(
            hall_sensor_pin=door_hall_sense_pin,
            left_encoder_pin=door_left_encoder_pin,
            right_encoder_pin=door_right_encoder_pin)
        door_sensor_temp.setup()
        door_sensor = door_sensor_temp

        print('BOOT: Server')
        import server
        server.enable_server(door_controller, door_sensor)

        print('BOOT: AP')
        import networkHelper
        networkHelper.setup_ap()

        print('BOOT: WiFi')
        networkHelper.try_connect()

        print('BOOT: NetworkTime')
        from networkTime import NetworkTime
        network_time = NetworkTime()

        print("BOOT: AWS")
        from awsClient import AwsClient
        temp_aws_client = AwsClient(door_controller, door_sensor, network_time)
        temp_aws_client.setup()
        aws_client = temp_aws_client

    except Exception as e:
        if loadingControl:
            loadingControl.set_detail(repr(e))
        sys.print_exception(e)
        raise


def background_loop():
    while True:
        try:
            if network_time:
                network_time.do_tasks()

            if door_sensor:
                door_sensor.do_tasks()

            if door_controller:
                door_controller.do_tasks()

            if aws_client:
                aws_client.do_tasks()

        except Exception as e:
            sys.print_exception(e)
        utime.sleep_ms(100)


_thread.start_new_thread(setup, ())
_thread.start_new_thread(background_loop, ())
