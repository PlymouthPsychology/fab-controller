
from collections import namedtuple


# We have two hands
HANDS = ['left', 'right']

# Pairs are a structure used to store values on each hand
Pair = namedtuple('Pair', HANDS)


# MOTOR PIN NUMBERS USING GPIO.BCM numbering
STEP_PIN = Pair(18, 23)
DIRECTION_PIN = Pair(24, 25)
HIGH_LIMIT_PIN = Pair(17, 22)
KILL_PIN = 4

# Delay between setting pin high and low when pulsing the stepper motors
STEP_DELAY = .0001


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


ALLOWABLE_DISCREPANCY = 5  # delta between sensor reading and target which triggers a movement


# SENSOR SETTINGS

# parameters for voltage to kg conversion
# intercepts (alpha) and slopes (beta)
# stored as pairs because sensor calibration may differ between components
ALPHA = Pair(-451.9, -595)
BETA = Pair(1121.427, 1149.319)


# Initialise the ADC device using the default addresses and sample rate,
# change this value if you have changed the address selection jumpers
SENSOR_CHANNEL_CODE = Pair(0x68, 0x69)
# Sample rate can be 12,14, 16 or 18
SENSOR_SAMPLE_RATE = 12


# How many values to store and smooth over
SMOOTHING_WINDOW = 10

# How often to poll the sensors themselves
SENSOR_POLL_INTERVAL = .01  # too cpu intensive if less than this?

# How often to calculate a new smoothed value
SENSOR_SMOOTHED_CALC_INTERVAL = .1  # .04


# CLIENT
LOG_INTERVAL = 1  # seconds
DASHBOARD_UPDATE_INTERVAL = .1
