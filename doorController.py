from _thread import allocate_lock
import sys
from workScheduler import WorkScheduler


class DoorController:

    def __init__(self, relayPin):
        self.relayPin = relayPin
        self.lock = allocate_lock()
        self.relayPin.off()
        self.turn_off_at = None
        self.turn_off_scheduler = WorkScheduler()

    def do_tasks(self):
        try:
            if self.turn_off_scheduler.work_pending(500):
                self.relayPin.off()

        except Exception as e:
            sys.print_exception(e)

    def toggle_door(self):
        self.turn_off_scheduler.schedule_work(500)
        self.relayPin.on()
