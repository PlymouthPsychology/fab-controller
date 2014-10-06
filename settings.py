
from collections import namedtuple


# We have two hands
HANDS = ['left', 'right']

# Pairs are a structure used to store values on each hand
Pair = namedtuple('Pair', HANDS)

Block = namedtuple('Block', ['duration', 'grams'])  # grams should be a pair


# PIN NUMBERS

STEP_PIN = Pair(2, 3)
DIRECTION_PIN = Pair(6, 7)

HIGH_LIMIT_PIN = Pair(14, 15)

# analog pins
SENSOR_PIN = Pair(4, 5)

# sensor readings at 2kg
TWO_KG = Pair(0.413, 0.443)


# KILL_PIN = 4


# Delay between setting pin high and low when pulsing the stepper motors
STEP_DELAY = .0004

# specify where CW is high or low when running motors
UP = 0
DOWN = 1
MOVEMENT_LABELS = {UP: 'up', DOWN: 'down'}
MOVEMENT = {v: k for k, v in MOVEMENT_LABELS.items()}

# We use micro stepping, so 8 pulses per full step of the motor
STEPS_PER_FULL_STEP = 8

FULL_STEPS_PER_REV = 200
STEPS_PER_REV = FULL_STEPS_PER_REV * STEPS_PER_FULL_STEP

# 5mm of travel per revolution of the motor shaft
MM_PER_REV = 5

# We don't want the motors to move more than this number of mm
MM_MAX_TRAVEL = 20
MAX_STEPS = (MM_MAX_TRAVEL / MM_PER_REV) * STEPS_PER_REV

ALLOWABLE_DISCREPANCY = 50  # delta between sensor reading and target which triggers a movement



# CLIENT
LOG_INTERVAL = 1  # seconds
DASHBOARD_UPDATE_INTERVAL = .1
SERVER_PORT = 2008
