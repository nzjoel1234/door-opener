from machine import Pin
import sys
from event import Event
from workScheduler import WorkScheduler


def enum(**enums):
    return type('Enum', (), enums)


DoorStates = enum(
    CLOSED='CLOSED',
    OPEN='OPEN',
    CLOSING='CLOSING',
    OPENING='OPENING')


EncoderPositions = [
    0b00,
    0b01,
    0b11,
    0b10,
]


def next_encoder_position(position):
    return (position + 1) % len(EncoderPositions)


stationary_timeout = 3000


class DoorSensor:

    def __init__(self, hall_sensor_pin: Pin, left_encoder_pin: Pin, right_encoder_pin: Pin):
        self.state_changed_event = Event()
        self.hall_sensor_pin = hall_sensor_pin
        self.left_encoder_pin = left_encoder_pin
        self.right_encoder_pin = right_encoder_pin
        self.stationary_scheduler = WorkScheduler()
        self.state = None
        self.encoder_position = None
        self.last_read_time = None

    def setup(self):
        self.on_state_change()

    def read_hall_sensor(self):
        return DoorStates.CLOSED if self.hall_sensor_pin.value() else DoorStates.OPEN

    def on_state_change(self, state: DoorStates = None):
        self.stationary_scheduler.schedule_work(stationary_timeout)
        state = state or self.read_hall_sensor()
        if state == DoorStates.OPEN and self.state == DoorStates.CLOSED:
            state = DoorStates.OPENING
        if self.state == state:
            return
        print('Door state changed: {}'.format(state))
        self.state = state
        self.state_changed_event.raise_event(self.state)

    def update_encoder(self):
        if self.read_hall_sensor() == DoorStates.CLOSED:
            self.on_state_change(DoorStates.CLOSED)
            return

        value = (
            (self.left_encoder_pin.value() << 1) +
            self.right_encoder_pin.value())
        position = EncoderPositions.index(value)

        if position == self.encoder_position:
            return

        last_position = self.encoder_position if self.encoder_position is not None else position
        self.encoder_position = position

        print('Encoder position: {}'.format(self.encoder_position))
        self.stationary_scheduler.schedule_work(stationary_timeout)

        if self.encoder_position == next_encoder_position(last_position):
            self.on_state_change(DoorStates.OPENING)
        elif next_encoder_position(self.encoder_position) == last_position:
            self.on_state_change(DoorStates.CLOSING)

    def do_tasks(self):
        try:
            self.update_encoder()

            if self.stationary_scheduler.work_pending(stationary_timeout):
                self.on_state_change()

        except Exception as e:
            sys.print_exception(e)
