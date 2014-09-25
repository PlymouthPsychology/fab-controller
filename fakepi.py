from settings import ALPHA

class FakeGPIO(object):

    HIGH = 1
    LOW = 0

    PINS = {i:0 for i in range(25)}

    def input(self, pin):
        return self.PINS[pin]

    def output(pin, val):
        self.PINS[pin] = val
        return None


class FakeADC(object):

    CHANNELS = {i: j for i, j in zip([1,2], [.4242, .5293])}

    def readVoltage(self, channel):
        return self.CHANNELS[channel]
