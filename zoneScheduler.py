from workScheduler import WorkScheduler
from sprinklerConfiguration import SprinklerConfiguration
from _thread import allocate_lock
from shiftR import ShiftR
import utime
import sys
from event import Event


class ZoneQueue:

    def __init__(self, active=[], pending=[]):
        self.active = list(active)
        self.pending = list(pending)

    def is_empty(self):
        return len(self.active) + len(self.pending) == 0

    def concat(self, new_items):
        return ZoneQueue(self.active, self.pending + new_items)

    def serialise(self):
        import json
        return json.dumps({
            'active': self.active,
            'pending': self.pending,
        })


class ZoneScheduler:

    def __init__(self, config: SprinklerConfiguration, shiftR: ShiftR):
        self.last_schedule_check = utime.time()
        self.config = config
        self.shiftR = shiftR
        self.queue = ZoneQueue()
        self.queue_lock = allocate_lock()
        self.workScheduler = WorkScheduler()
        self.workScheduler.schedule_work()
        self.on_change_handler = lambda: self.workScheduler.schedule_work()
        self.config.on_change_event.add_handler(
            self.on_change_handler)
        self.queue_changed_event = Event()

    def __del__(self):
        if self.config and self.on_change_handler:
            self.config.on_change_event.remove_handler(
                self.on_change_handler)

    def is_active(self):
        return not self.queue.is_empty()

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

            with self.queue_lock:
                # remove items which have completed
                new_active_queue = list(filter(
                    lambda z: z[1] > now,
                    self.queue.active))

                active_groups = [
                    z.group
                    for z in [
                        self.config.get_zone(i[0])
                        for i in new_active_queue
                    ]
                    if z.group is not None
                ]

                new_pending_queue = []
                for pending in self.queue.pending:
                    zone_id, duration_s = pending
                    zone = self.config.get_zone(zone_id)
                    if not zone or duration_s <= 0:
                        continue
                    if zone.group in active_groups or any([z for z in new_active_queue if z[0] == zone.id]):
                        new_pending_queue.append(pending)
                        continue
                    if zone.group is not None:
                        active_groups.append(zone.group)
                    new_active_queue.append((zone_id, now + 1 + duration_s))

                self.queue = ZoneQueue(new_active_queue, new_pending_queue)
                self.queue_changed_event.raise_event(self.queue)

                self.shiftR.set_enabled(True)
                self.shiftR.set_enabled_outputs(list(map(
                    lambda z: z[0],
                    self.queue.active)))

                next_expiry = None
                if len(self.queue.active):
                    next_expiry = min(map(lambda z: z[1], self.queue.active))

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

    def stop_zones(self, zones=[]):
        with self.queue_lock:
            self.queue = ZoneQueue() \
                if zones is None or len(zones) == 0 else \
                    ZoneQueue(
                        filter(lambda i: i[0] not in zones, self.queue.active),
                        filter(lambda i: i[0] not in zones, self.queue.pending))
        self.workScheduler.schedule_work()

    def queue_zones(self, duration_by_zone):
        with self.queue_lock:
            self.queue = self.queue.concat(list(duration_by_zone.items()))
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
