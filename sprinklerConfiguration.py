class SprinklerConfiguration:

    last_manual_run = {}

    def save_last_manual_run(self, last_manual_run):
        self.last_manual_run = last_manual_run

    def get_zone_num(self):
        return 8

    def get_zone_name(self, zone_id):
        if zone_id == 0:
            return 'Front lawn'
        if zone_id == 1:
            return 'Back lawn'
        return 'Zone {}'.format(zone_id + 1)

    def get_zones(self):
        return list(map(
            lambda id: (id, self.get_zone_name(id)),
            range(self.get_zone_num())))

    def get_program(self, program_id):
        matching = list(
            filter(lambda p: p[0] == program_id, self.get_programs()))
        return matching[0] if any(matching) else None

    def get_programs(self):
        return list(map(
            lambda id: (id, 'Program {}'.format(id)),
            range(3)))

    def get_next_schedule_time(self, schedule):
        schedule = {
            'type': 1,  # N days
        }

    def get_program_zones(self, program_id):
        if program_id == 0:
            return {
                0: 5,
                2: 10,
                4: 5,
                6: 15,
            }
        elif program_id == 1:
            return {
                1: 5,
                3: 10,
                5: 5,
                7: 15,
            }
        else:
            return {
                1: 1,
                2: 2,
                3: 3,
                4: 4,
                5: 5,
                6: 6,
                7: 7,
            }

    def get_group_id_by_zone(self, zone_id):
        if zone_id == 6 or zone_id == 7:
            return 1
        return None


instance = None


def setup():
    global instance
    instance = SprinklerConfiguration()
    return instance
