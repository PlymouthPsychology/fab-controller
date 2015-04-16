import os
from collections import namedtuple
import random
import pkg_resources  # part of setuptools


FAB_VERSION = pkg_resources.require("fab_controller")[0].version

HANDS = ['left', 'right']  # We have two hands
Pair = namedtuple('Pair', HANDS)  # structure used to store values on each hand
Block = namedtuple('Block', ['duration', 'grams', 'prompt'],)  # grams should itself be a Pair


# FOR TWEAKING

LOG_INTERVAL = .5
LOGFILE_DIR = os.path.expanduser("~/FAB/logs/")

REST_N_FROM_TOP = 500

STEP_DELAY = .0003  # Delay between setting pin high and low when pulsing the stepper motors
TIGHT_LOOP_INTERVAL = .001  # delay after running each iteration of the tracking loop
# Note, by default the sensor values are updated every 0.001 of a second by the Iterator instance
# see https://github.com/tino/pyFirmata/blob/master/pyfirmata/util.py#L38
# However firmata only updates every 19ms, so this may be spuriously accurate
# this gives a theoretical speed of ~3mm of travel per second because 5*(1000/8/200)

ALLOWABLE_DISCREPANCY = 20  # delta between sensor reading and target which triggers a movement
TWO_KG = Pair(0.4457, 0.4692)  # sensor readings at 2kg load - these need to be measured!!!
DASHBOARD_UPDATE_INTERVAL = .2
SERVER_PORT = 2008 #random.choice(range(2000, 10000))


# PROBABLY BEST LEFT

STEP_PIN = Pair(2, 3)
DIRECTION_PIN = Pair(6, 7)
HIGH_LIMIT_PIN = Pair(17, 18)
LOW_LIMIT_PIN = Pair(15, 16)
SENSOR_PIN = Pair(4, 5)  # note these are the analog pins


UP = 0  # specify direction of rotation
DOWN = 1
MOVEMENT_LABELS = {UP: 'up', DOWN: 'down'}
MOVEMENT = {v: k for k, v in list(MOVEMENT_LABELS.items())}
STEPS_PER_FULL_STEP = 8  # We use micro stepping, so 8 pulses per full step of the motor
FULL_STEPS_PER_REV = 200
STEPS_PER_REV = FULL_STEPS_PER_REV * STEPS_PER_FULL_STEP
MM_PER_REV = 5  # 5mm of travel per revolution of the motor shaft
MM_MAX_TRAVEL = 15  # We don't want the motors to move more than this number of mm
MAX_REVS = MM_MAX_TRAVEL / MM_PER_REV
MAX_STEPS = MAX_REVS * STEPS_PER_REV



SWITCH_CHECKING_WINDOW_LENGTH = 5
SENSOR_MEASUREMENTS_WINDOW_LENGTH = 5    # number of weight samples to take 
										 # Note, this number was based on some 
										 # experimentation - less than 5
 
