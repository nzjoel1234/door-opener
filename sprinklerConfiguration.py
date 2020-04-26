from collections import namedtuple
import sys
import json
import time


def get_value(d, key, default=None):
    return d[key] if d is not None and key in d else default

Zone = namedtuple('Zone', ('id', 'name', 'group'))

def parse_zone(id, config):
    name = get_value(config, 'name', default='Zone {}'.format(id + 1))
    group = get_value(config, 'group')
    return Zone(id, name, group)

def parse_zones(config):
    return sorted([
        parse_zone(int(key), config[key])
        for key in config.keys()
    ], key=lambda z: z.id)

Program = namedtuple('Program', ('id', 'name', 'zones', 'schedules'))
ZoneDuration = namedtuple('ZoneDuration', ('id', 'duration'))
Schedule = namedtuple('ProgramZone', (
    'start_time',
    'odd_days',
    'even_days',
    'week_days'))

def parse_program(id, config):
    name = get_value(config, 'name', default='Program {}'.format(id + 1))
    zones = [
        ZoneDuration(
            get_value(z_config, 'id'),
            get_value(z_config, 'duration'))
            for z_config in get_value(config, 'zones', default=[])]
    schedules = [
        Schedule(
            get_value(s_config, 'start_time'),
            get_value(s_config, 'odd_days', default=True),
            get_value(s_config, 'even_days', default=True),
            get_value(s_config, 'week_days', default=[]))
            for s_config in get_value(config, 'schedules', default=[])]
    return Program(id, name, zones, schedules)

def parse_programs(config):
        return sorted([
            parse_program(i, x)
            for i, x in enumerate(config)
        ], key=lambda p: p.id)

Config = namedtuple('Config', ('zones', 'programs'))

def parse_config(config):
    if not config:
        return None
    return Config(
        parse_zones(get_value(config, 'zones', default=[])),
        parse_programs(get_value(config, 'programs', default={})))


def get_item_by_id(items, id):
    try:
        return next((i for i in items if i.id == id))
    except StopIteration:
        return None


class SprinklerConfiguration:

    config = None
    last_manual_run = {}

    def save_last_manual_run(self, last_manual_run):
        self.last_manual_run = last_manual_run

    def load_config(self, forceReload=False):
        if forceReload or self.config is None:
            try:
                self.config = None
                with open('sprinkler_config.json', 'r') as f:
                    self.config = parse_config(json.loads(f.read()))
            except Exception as e:
                sys.print_exception(e)
                self.config = None
        return self.config

    def get_zone_num(self):
        return 8

    def get_zones(self):
        return self.config.zones if self.config else []

    def get_zone(self, id):
        return get_item_by_id(self.get_zones(), id)

    def get_programs(self):
        return self.config.programs if self.config else []

    def get_program(self, id):
        return get_item_by_id(self.get_programs(), id)

    def get_next_program_start(self, program, since_secs):
        if not program or not any(program.schedules):
            return None
        y, mo, d, h, mi, s, wd, *z = time.localtime(since_secs)
        day_start_secs = time.mktime((y, mo, d, 0, 0, 0, 0, 0))
        day = 0
        while day < 7:
            for s in sorted(program.schedules, key=lambda s: s.start_time):
                start_time_h = round(s.start_time / 100)
                start_time_m = s.start_time % 100
                start_secs = day_start_secs + \
                    (start_time_h * 60 + start_time_m) * 60
                if start_secs <= since_secs:
                    continue
                is_even = (d % 2) == 0
                if is_even and not s.even_days:
                    continue
                if not is_even and not s.odd_days:
                    continue
                if any(s.week_days) and wd not in s.week_days:
                    continue
                return start_secs
            day += 1
            day_start_secs = day_start_secs + 24 * 60 * 60
            y, mo, d, h, mi, s, wd, yd = time.localtime(day_start_secs)
        return None


instance = None


def setup():
    global instance
    instance = SprinklerConfiguration()
    instance.load_config()
    return instance
