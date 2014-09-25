from settings import *
import time


def kg_from_v(v, hand):
    """Convert using regression parameters in settings.
    Note parameters for each hand/sensor may differ."""
    return getattr(ALPHA, hand) + getattr(BETA, hand) * v


def weights(adc):
    """Return a pair containing current calculated weight values."""
    return Pair(
        kg_from_v(adc.readVoltage(1), 'left'),
        kg_from_v(adc.readVoltage(2), 'right'),
    )


def weight_stream(adc):
    """Generator yielding pairs of kg readings from and ADC."""
    while True:
        yield weights(adc=adc)
        time.sleep(0.001)


def read(pin):
    return GPIO.input(pin)


def write(pin, val):
    GPIO.output(pin, val)
    return val


def pulse(hand, delay=STEP_DELAY):
    write(getattr(STEP_PIN, hand), GPIO.HIGH)
    time.sleep(delay)
    write(getattr(STEP_PIN, hand), GPIO.LOW)
    time.sleep(delay)
