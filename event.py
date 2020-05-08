import sys


class Event:

    def __init__(self):
        self.handlers = []

    def add_handler(self, handler):
        self.handlers.append(handler)

    def remove_handler(self, handler):
        self.handlers.remove(handler)

    def raise_event(self, *args):
        for handler in self.handlers:
            try:
                handler(*args)
            except Exception as e:
                sys.print_exception(e)
