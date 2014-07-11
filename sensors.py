import math
import random
import gevent
from client import app
from fakeworld import sensor_noise, steps_from_top, pin_states
from pins import *
from utils import *


def at_top_limit(hand):
    """XXX need to make this real and test a pin attached to microswitch"""
    # thepin = MOTOR_PINS[hand]['kill']
    # return bool(digital_read[thepin] != 0)
    return bool(steps_from_top[hand] == 0)


def at_bottom_limit(hand):
    return bool(steps_from_top[hand] < MAX_STEPS)

    
def _measure_pin(hand):
    """# TODO fix this to get real measures from GPIO"""
    #return digital_read(SENSOR_PINS[hand] 
    position = steps_from_top[hand]
    if position < 500:
        reading = 0
    else:
        reading = scale_to_new_range(position, (500, MAX_STEPS), (0, 100)) 
    return reading + sensor_noise()
    

def poll_sensors():
    """Check the sensor readings and update app state."""
    while True:
        app.measurements['left'].append(_measure_pin('left'))
        app.measurements['right'].append(_measure_pin('right'))
        gevent.sleep(SENSOR_POLL_INTERVAL)



av = lambda x: sum(x)/SMOOTHING_WINDOW



# pre-calculate decay function weights to smooth sensor input
_tmp = [i**2 for i in range(SMOOTHING_WINDOW)]
SMOOTHING_CURVE = [scale_to_new_range(i, (min(_tmp), max(_tmp))) for i in _tmp]  # scale it back to 0..1


def smoother(x):
    if not x:
        return 0
    return sum([i*j for i, j in zip(x, SMOOTHING_CURVE)])/len(x) or 0


def smooth_current_sensor_values(func=av):
    """Calculate the current sensor readings, perhaps using smoothing function."""
    while True:
        newvals = {
            'left': func(app.measurements['left']),
            'right': func(app.measurements['right']),
        }
        app.smoothed.update(newvals)
        gevent.sleep(SENSOR_SMOOTHED_CALC_INTERVAL)
    
    
    