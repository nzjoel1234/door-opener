import utime


class WorkScheduler:

    def __init__(self):
        self.run_scheduled = False
        self.next_run = None

    def schedule_work(self, millis=0):
        self.next_run = utime.ticks_add(utime.ticks_ms(), millis)
        self.run_scheduled = True

    def work_pending(self):
        work_pending = self.run_scheduled and utime.ticks_diff(
            utime.ticks_ms(), self.next_run) >= 0
        if work_pending:
            self.run_scheduled = False
        return work_pending
