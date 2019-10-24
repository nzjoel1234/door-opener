class ShiftR:

    # s = ShiftR(Pin(26, Pin.OUT), Pin(14, Pin.OUT), Pin(13, Pin.OUT), Pin(27, Pin.OUT), 8)
    def __init__(self, pin_output_enable, pin_clk, pin_ser, pin_latch, n_outputs):
        self.pin_output_enable = pin_output_enable
        self.pin_clk = pin_clk
        self.pin_ser = pin_ser
        self.pin_latch = pin_latch
        self.n_outputs = n_outputs

    def setup(self):
        self.set_enabled_outputs([])
        self.set_enabled(True)

    def set_enabled(self, enabled):
        # set pin LOW to enable outputs
        self.pin_output_enable.value(0 if enabled else 1)

    def force_disable(self):
        try:
            self.set_enabled_outputs([])
        except:
            pass
        try:
            self.set_enabled(False)
        except:
            pass

    def set_enabled_outputs(self, enabled_outputs):
        self.pin_latch.off()
        for i in range(self.n_outputs):
            self.pin_clk.off()
            self.pin_ser.value(0 if i in enabled_outputs else 1)
            self.pin_clk.on()
        self.pin_latch.on()
