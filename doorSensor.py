from micropython import schedule
from machine import Pin
import sys
from event import Event
from workScheduler import WorkScheduler
import utime


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


encoder_debounce_limit = 3


class DoorSensor:

    def __init__(self, hall_sensor_pin: Pin, left_encoder_pin: Pin, right_encoder_pin: Pin):
        self.state_changed_event = Event()
        self.hall_sensor_pin = hall_sensor_pin
        self.left_encoder_pin = left_encoder_pin
        self.right_encoder_pin = right_encoder_pin
        self.refresh_state_scheduler = WorkScheduler()
        self.state = None
        self.encoder_position = None
        self.last_encoder_position = None
        self.encoder_buffer = 0
        self.encoder_schedule_handler = \
            lambda x: self.on_encoder_changed()
        self.last_read_time = None

    def setup(self):
        self.left_encoder_pin.irq(
            trigger=Pin.IRQ_RISING |
            Pin.IRQ_FALLING, handler=self.encoder_irq_handler)
        self.right_encoder_pin.irq(
            trigger=Pin.IRQ_RISING |
            Pin.IRQ_FALLING, handler=self.encoder_irq_handler)
        self.encoder_position = self.read_encoder_position()
        self.last_encoder_position = self.encoder_position
        self.on_state_change()

    def on_state_change(self, state: DoorStates = None):
        self.refresh_state_scheduler.schedule_work(3000)
        state = state or (
            DoorStates.CLOSED if self.hall_sensor_pin.value() else DoorStates.OPEN)
        if state == DoorStates.OPEN and self.state == DoorStates.CLOSED:
            state = DoorStates.OPENING
        if state == DoorStates.OPEN or state == DoorStates.CLOSED:
            self.encoder_buffer = 0
        if self.state == state:
            return
        print('Door state changed: {}'.format(state))
        self.state = state
        self.state_changed_event.raise_event(self.state)

    def read_encoder_position(self, desc=' '):
        value = (
            (self.left_encoder_pin.value() << 1) +
            self.right_encoder_pin.value())
        read_time = utime.ticks_ms()
        read_delta = utime.ticks_diff(
            read_time, self.last_read_time) if self.last_read_time else 0
        print('Encoder value: {:02b} {} ({})'.format(value, desc, read_delta))
        self.last_read_time = read_time
        return EncoderPositions.index(value)

    def encoder_irq_handler(self, pin):
        if self.hall_sensor_pin.value():
            return
        position = self.read_encoder_position(
            'L' if pin == self.left_encoder_pin else 'R')
        if position == self.encoder_position:
            return
        self.refresh_state_scheduler.schedule_work(3000)
        self.encoder_position = position
        schedule(self.encoder_schedule_handler, 0)

    def on_encoder_changed(self):

        if self.hall_sensor_pin.value():
            self.encoder_buffer = 0
            self.on_state_change(DoorStates.CLOSED)
            return

        if self.last_encoder_position == self.encoder_position:
            return

        prev_position = self.last_encoder_position
        self.last_encoder_position = self.encoder_position

        print('Encoder position: {}'.format(self.encoder_position))
        self.refresh_state_scheduler.schedule_work(3000)

        if self.encoder_position == next_encoder_position(prev_position):
            self.encoder_buffer = min(
                encoder_debounce_limit,
                self.encoder_buffer + 1)
        elif next_encoder_position(self.encoder_position) == prev_position:
            self.encoder_buffer = max(
                -encoder_debounce_limit,
                self.encoder_buffer - 1)

        if abs(self.encoder_buffer) < encoder_debounce_limit:
            return

        self.on_state_change(
            DoorStates.OPENING if self.encoder_buffer > 0 else DoorStates.CLOSING)

    def do_tasks(self):
        try:
            if self.refresh_state_scheduler.work_pending(3000):
                self.on_state_change()

        except Exception as e:
            sys.print_exception(e)
