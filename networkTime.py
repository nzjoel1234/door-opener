import sys
from workScheduler import WorkScheduler
import networkHelper


class NetworkTime:

    def __init__(self):
        self.ntp_loaded = False
        self.workScheduler = WorkScheduler(True)

    def do_tasks(self):
        if self.ntp_loaded or not self.workScheduler.work_pending(1000):
            return
        try:
            import networkHelper
            if not networkHelper.isWiFiActive():
                return
            import ntptime
            ntptime.settime()
            self.ntp_loaded = True
            print('ntp loaded')
        except Exception as e:
            sys.print_exception(e)
