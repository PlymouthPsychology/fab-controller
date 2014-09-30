import gevent
import math
from functools import partial
from programs import set_block_targets
from sensors import at_top_limit
from settings import *
from utils import *
from py_io import *


def _get_direction(hand):
    return digital_read(MOTOR_PINS[hand]['direction'])


def _calculate_increment(hand):
    return _get_direction(hand) and 1 or -1


def _increment_step_count(hand):
    steps_from_top[hand] += _calculate_increment(hand)


def _set_direction(hand, direction):
    digital_write(MOTOR_PINS[hand]['direction'], direction)
    MOTOR_PINS[hand]['direction'] = direction


def _step_motor(hand):
    nexposwouldbe = steps_from_top[hand] + _calculate_increment(hand)
    if nexposwouldbe >= 0 and nexposwouldbe < MAX_STEPS:
        _increment_step_count(hand)
        digital_write(MOTOR_PINS[hand]['step'], 1)
    else:
        # print "tried to step out of line {}".format(nexposwouldbe)
        pass


def run_motors_to_top_stop():
    _set_direction('left', UP)
    _set_direction('right', UP)
    print "Resetting motors"
    while not at_top_limit('left') or not at_top_limit('right'):
        _step_motor('left')
        _step_motor('right')
        gevent.sleep(0)


def run_motor_to_maintain_constant_force(hand):
    while True:
        # larger delta means we need more force pressing down
        delta = app.targets[hand] - app.smoothed[hand]
        adelta = abs(delta)
        if adelta > ALLOWABLE_DISCREPANCY:
            # decide which direction
            if delta > 0:
                _set_direction(hand, UP)
            else:
                _set_direction(hand, DOWN)

            gevent.spawn(_step_motor, *(hand,))

        # longer pause between step as we get closer to target
        delay = adelta > 3 and .0005 or adelta > 1 and .005 or adelta > .1 and .05 or .2
        gevent.sleep(delay)

# make functions for L and R which can be joined independently to the event loop
run_left = partial(run_motor_to_maintain_constant_force, 'left')
run_right = partial(run_motor_to_maintain_constant_force, 'right')
