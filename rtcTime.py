import sys
import utime
from ds3231_port import DS3231
from workScheduler import WorkScheduler


class RtcTime:
    
    def __init__(self):
        self.ds3231 = None
        self.ntp_loaded = False
        self.workScheduler = WorkScheduler()

    def setup(self, i2c):
        ds3231 = DS3231(i2c)
        ds3231.get_time(set_rtc=True)
        self.ds3231 = ds3231
        self.workScheduler.schedule_work()

    def do_tasks(self):
        if self.ntp_loaded or not self.workScheduler.work_pending(5000):
            return
        try:
            import ntptime
            ntptime.settime()
            self.ds3231.save_time()
            self.ntp_loaded = True
            print('ntp loaded')
        except Exception as e:
            sys.print_exception(e)
