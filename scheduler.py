from workScheduler import WorkScheduler
from sprinklerConfiguration import SprinklerConfiguration
from _thread import allocate_lock
from shiftR import ShiftR
import utime
import sys


class Scheduler:

    def __init__(self, config: SprinklerConfiguration, shiftR: ShiftR):
        self.last_schedule_check = utime.time()
        self.config = config
        self.shiftR = shiftR
        self.pending_queue = []  # List[Tuple[Zone_id, Duration_Secs]]
        self.active_queue = []  # List[Tuple[Zone_id, End_Time_Secs]]
        self.queue_lock = allocate_lock()
        self.workScheduler = WorkScheduler()
        self.workScheduler.schedule_work()

    def is_active(self):
        with self.queue_lock:
            return len(self.active_queue) > 0 or len(self.pending_queue) > 0

    def stop_all(self):
        with self.queue_lock:
            self.pending_queue = []
            self.active_queue = []
            self.workScheduler.schedule_work()

    def do_tasks(self):
        if not self.workScheduler.work_pending():
            return

        try:
            now = utime.time()

            if now > self.last_schedule_check:
                # see if any scheduled programs are ready to be added to pending queue
                program_ids = self.get_program_starts_between_times(
                    self.last_schedule_check, now)

                if program_ids is not None:
                    for program_id in program_ids:
                        self.queue_program(program_id)

                self.last_schedule_check = now

            # remove items which have completed
            self.active_queue = list(filter(
                lambda z: z[1] > now,
                self.active_queue))

            active_group_ids = list(filter(
                lambda g: g is not None,
                map(lambda z: self.config.get_group_id_by_zone(z[0]),
                    self.active_queue)))

            with self.queue_lock:
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
                    self.active_queue.append((zone_id, now + 1 + duration_s))
                self.pending_queue = new_pending_queue

            self.shiftR.set_enabled(True)
            self.shiftR.set_enabled_outputs(list(map(
                lambda z: z[0],
                self.active_queue)))

            next_expiry = None
            if len(self.active_queue):
                next_expiry = min(map(lambda z: z[1], self.active_queue))

            next_start = self.get_next_start_time(now)

            if next_start is None:
                next_work = next_expiry
            elif next_expiry is None:
                next_work = next_start
            else:
                next_work = min([next_start, next_expiry])

            if next_work is not None:
                self.workScheduler.schedule_work(
                    (next_work - utime.time()) * 1000 + 1)

        except Exception as e:
            sys.print_exception(e)
            try:
                self.shiftR.set_enabled_outputs([])
            except Exception as ex:
                sys.print_exception(ex)
                self.shiftR.force_disable()
            self.workScheduler.schedule_work(2000)

    def queue_zones(self, duration_by_zone):
        with self.queue_lock:
            for item in duration_by_zone.items():
                self.pending_queue.append(item)
        self.workScheduler.schedule_work()

    def queue_zone(self, zone_id, duration_s):
        self.queue_zones({zone_id: duration_s})

    def queue_program(self, program_id: int):
        self.queue_zones(self.config.get_program_zones(program_id))

    def get_next_start_time(self, since_secs):
        programs_schedule_in = list(
            filter(
                lambda s: s is not None,
                [self.config.get_next_program_start(id, since_secs) for id in self.config.get_program_ids()]))
        if not any(programs_schedule_in):
            return None
        return sorted(programs_schedule_in)[0]

    def get_program_start_times_between_times(self, program_id, since_secs, until_secs):
        times = []
        t = since_secs
        while True:
            start_time = self.config.get_next_program_start(program_id, t)
            if start_time is None or start_time > until_secs:
                return times
            times.append(times)
            t = start_time + 1

    def get_program_starts_between_times(self, since_secs, until_secs):
        res = []
        for program_id in self.config.get_program_ids():
            for start_time in self.get_program_start_times_between_times(program_id, since_secs, until_secs):
                res.append((program_id, start_time))
        return list(map(lambda i: i[0], sorted(res, key=lambda i: i[1])))


instance = None


def setup(config: SprinklerConfiguration, shiftR: ShiftR):
    global instance
    instance = Scheduler(config, shiftR)
    return instance
