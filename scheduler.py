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
                starts = self.get_starts_between_times(
                    self.last_schedule_check, now)

                if starts is not None:
                    for start in starts:
                        self.queue_program(start[1])

                self.last_schedule_check = now

            # remove items which have completed
            self.active_queue = list(filter(
                lambda z: z[1] > now,
                self.active_queue))

            active_groups = [
                z.group
                for z in [
                    self.config.get_zone(i[0])
                    for i in self.active_queue
                ]
                if z.group is not None
            ]

            with self.queue_lock:
                new_pending_queue = []
                for pending in self.pending_queue:
                    zone_id, duration_s = pending
                    zone = self.config.get_zone(zone_id)
                    if not zone or duration_s <= 0:
                        continue
                    if zone.group in active_groups or any([z for z in self.active_queue if z[0] == zone.id]):
                        new_pending_queue.append(pending)
                        continue
                    if zone.group is not None:
                        active_groups.append(zone.group)
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

    def queue_program(self, program_id):
        program = self.config.get_program(program_id)
        if not program:
            return
        self.queue_zones({
            z.id: z.duration
            for z in program.zones
        })

    def get_next_start_time(self, since_secs):
        programs_schedule_in = [
            s for s in [
                self.config.get_next_program_start(p, since_secs)
                for p in self.config.get_programs()
            ] if s is not None
        ]
        if not any(programs_schedule_in):
            return None
        return sorted(programs_schedule_in)[0]

    def get_program_start_times_between_times(self, program, since_secs, until_secs):
        times = []
        t = since_secs
        while True:
            start_time = self.config.get_next_program_start(program, t)
            if start_time is None or start_time > until_secs:
                return times
            times.append(times)
            t = start_time + 1

    def get_starts_between_times(self, since_secs, until_secs):
        return sorted([item for sublist in [
            [
                (start_time, program.id)
                for start_time in
                self.get_program_start_times_between_times(
                    program, since_secs, until_secs)
            ]
            for program in self.config.get_programs()
        ] for item in sublist], key=lambda i: i[0])


        [item for sublist in l for item in sublist]


instance = None


def setup(config: SprinklerConfiguration, shiftR: ShiftR):
    global instance
    instance = Scheduler(config, shiftR)
    return instance
