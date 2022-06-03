import sys
from workScheduler import WorkScheduler


class NetworkTime:

    def __init__(self):
        self.ntp_loaded = False
        self.workScheduler = WorkScheduler(True)

    def do_tasks(self):
        if self.ntp_loaded or not self.workScheduler.work_pending(5000):
            return
        try:
            import ntptime
            ntptime.settime()
            self.ntp_loaded = True
            print('ntp loaded')
        except Exception as e:
            sys.print_exception(e)
