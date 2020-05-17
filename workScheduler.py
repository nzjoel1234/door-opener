import utime


class WorkScheduler:

    def __init__(self, schedule=False):
        self.run_scheduled = False
        self.next_run = None
        if schedule:
            self.schedule_work()

    def schedule_work(self, millis=0):
        self.next_run = utime.ticks_add(utime.ticks_ms(), millis)
        self.run_scheduled = True

    def work_pending(self, millis=None):
        work_pending = self.run_scheduled and utime.ticks_diff(
            utime.ticks_ms(), self.next_run) >= 0
        if work_pending:
            self.run_scheduled = False
            if millis is not None:
                self.schedule_work(millis)
        return work_pending
