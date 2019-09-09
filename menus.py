import ui


class menu_base:

    def __init__(self, items, goto):
        self.index = 0
        self.items = items
        self.goto = goto

    def render(self):
        ui.menu(list(map(lambda item: item[0], self.items)), self.index)

    def on_down(self):
        if self.index < len(self.items) - 1:
            self.index += 1
            self.render()

    def on_up(self):
        if self.index > 0:
            self.index -= 1
            self.render()

    def on_select(self):
        self.goto(self.items[self.index][1]())

    def get_root_menu(goto):
        return menu_base([
            ('Programs', lambda: menu_base.get_programs_menu(goto)),
            ('Info', lambda: menu_base.get_info_menu(goto)),
        ], goto)

    def get_programs_menu(goto):
        return menu_base([
            ('Back', lambda: menu_base.get_root_menu(goto)),
            ('Program 1', lambda: menu_base.get_root_menu(goto)),
            ('Program 2', lambda: menu_base.get_root_menu(goto)),
        ], goto)

    def get_info_menu(goto):
        return menu_base([
            ('Back', lambda: menu_base.get_root_menu(goto)),
            ('WiFi Status', lambda: menu_base.get_root_menu(goto)),
            ('Hotspot Status', lambda: menu_base.get_root_menu(goto)),
        ], goto)

    def get_wifi_status_menu(goto):
        return menu_base([
            ('Back', lambda: menu_base.get_root_menu(goto)),
        ])
