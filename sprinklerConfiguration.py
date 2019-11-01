import sys
import json
import utime


def get_value(d, key, default=None):
    return d[key] if d is not None and key in d else default


class SprinklerConfiguration:

    config = None
    last_manual_run = {}

    def save_last_manual_run(self, last_manual_run):
        self.last_manual_run = last_manual_run

    def get_config(self):
        if self.config is None:
            try:
                with open('sprinkler_config.json', 'r') as f:
                    self.config = json.loads(f.read())
            except Exception as e:
                sys.print_exception(e)
                self.config = None
        return self.config

    def get_zone_num(self):
        config = self.get_config()
        return get_value(config, 'max_zones', default=8)

    def get_zones_config(self):
        config = self.get_config()
        return get_value(config, 'zones', default={})

    def get_zone_ids(self):
        zones = self.get_zones_config()
        return sorted([int(key) for key in zones.keys()])

    def get_zone_config(self, zone_id):
        zones = self.get_zones_config()
        return get_value(zones, str(zone_id))

    def get_zone_name(self, zone_id):
        zone = self.get_zone_config(zone_id)
        return get_value(zone, 'name', default='Zone {}'.format(zone_id + 1))

    def get_group_id_by_zone(self, zone_id):
        zone = self.get_zone_config(zone_id)
        return get_value(zone, 'group', default=None)

    def get_programs_config(self):
        config = self.get_config()
        return get_value(config, 'programs', default=[])

    def get_program_ids(self):
        programs = self.get_programs_config()
        return sorted([i for i, x in enumerate(programs)])

    def get_program_config(self, program_id):
        programs = self.get_programs_config()
        return programs[program_id] if program_id < len(programs) else None

    def get_program_name(self, program_id):
        program = self.get_program_config(program_id)
        return get_value(program, 'name', default='Program {}'.format(program_id))

    def get_next_program_start(self, program_id, since_secs):
        program = self.get_program_config(program_id)
        schedules = get_value(program, 'schedules', [])
        if not any(schedules):
            return None
        schedules = sorted(schedules, key=lambda s: s['start_time'])
        y, mo, d, h, mi, s, wd, yd = utime.localtime(since_secs)
        day_start_secs = utime.mktime((y, mo, d, 0, 0, 0, 0, 0))
        day = 0
        while day < 7:
            for s in schedules:
                start_time = s['start_time']
                start_time_h = round(start_time / 100)
                start_time_m = start_time % 100
                start_secs = day_start_secs + \
                    (start_time_h * 60 + start_time_m) * 60
                if start_secs <= since_secs:
                    continue
                is_even = (d % 2) == 0
                if is_even and 'even_days' in s and not s['even_days']:
                    continue
                if not is_even and 'odd_days' in s and not s['odd_days']:
                    continue
                if 'week_days' in s and any(s['week_days']) and wd not in s['week_days']:
                    continue
                return start_secs
            day += 1
            day_start_secs = day_start_secs + 24 * 60 * 60
            y, mo, d, h, mi, s, wd, yd = utime.localtime(day_start_secs)
        return None

    def get_program_zones(self, program_id):
        """Returns { zone_id: duration }"""
        program = self.get_program_config(program_id)
        zones = get_value(program, 'zones', default={})
        res = {}
        for zone in zones:
            res[int(zone['id'])] = zone['duration']
        return res


instance = None


def setup():
    global instance
    instance = SprinklerConfiguration()
    return instance
