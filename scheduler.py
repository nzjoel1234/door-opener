from workScheduler import WorkScheduler
from sprinklerConfiguration import SprinklerConfiguration
from _thread import allocate_lock
from shiftR import ShiftR
import utime


class Scheduler:

    def __init__(self, config: SprinklerConfiguration, shiftR: ShiftR):
        self.config = config
        self.shiftR = shiftR
        self.pending_queue = []  # List[Tuple[Zone_id, Duration_Secs]]
        self.active_queue = []  # List[Tuple[Zone_id, End_Time_Secs]]
        self.pending_queue_lock = allocate_lock()
        self.workScheduler = WorkScheduler()
        self.workScheduler.schedule_work()

    def do_tasks(self):
        if not self.workScheduler.work_pending():
            return

        try:
            now = utime.time()

            # remove items which have completed
            self.active_queue = list(filter(
                lambda z: z[1] > now,
                self.active_queue))

            active_group_ids = list(filter(
                lambda g: g is not None,
                map(lambda z: self.config.get_group_id_by_zone(z[0]),
                    self.active_queue)))

            with self.pending_queue_lock:
                new_pending_queue = []
                for pending in self.pending_queue:
                    zone_id, duration_s = pending
                    if duration_s <= 0:
                        continue
                    group_id = self.config.get_group_id_by_zone(zone_id)
                    if group_id in active_group_ids or zone_id in map(lambda z: z[0], self.active_queue):
                        new_pending_queue.append(pending)
                        continue
                    if group_id is not None:
                        active_group_ids.append(group_id)
                    self.active_queue.append((zone_id, now + duration_s))
                self.pending_queue = new_pending_queue

            self.shiftR.set_enabled(True)
            self.shiftR.set_enabled_outputs(list(map(
                lambda z: z[0],
                self.active_queue)))

            if len(self.active_queue):
                next_expiry = min(map(lambda z: z[1] - now, self.active_queue))
                self.workScheduler.schedule_work(next_expiry * 1000)

        except Exception as e:
            print('service_queue error: {}'.format(repr(e)))
            try:
                self.shiftR.set_enabled_outputs([])
            except:
                print('Error disabling outputs: {}'.format(repr(e)))
                self.shiftR.force_disable()
            self.workScheduler.schedule_work(2000)

    def queue_zones(self, duration_by_zone):
        with self.pending_queue_lock:
            for item in duration_by_zone.items():
                self.pending_queue.append(item)
        self.workScheduler.schedule_work()

    def queue_zone(self, zone_id, duration_s):
        self.queue_zones({zone_id: duration_s})

    def queue_program(self, program_id: int):
        self.queue_zones(self.config.get_program_zones(program_id))


instance = None


def setup(config: SprinklerConfiguration, shiftR: ShiftR):
    global instance
    instance = Scheduler(config, shiftR)
    return instance
