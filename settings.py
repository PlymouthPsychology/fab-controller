from collections import namedtuple

HANDS = ['left', 'right']  # We have two hands
Pair = namedtuple('Pair', HANDS)  # structure used to store values on each hand
Block = namedtuple('Block', ['duration', 'grams'])  # grams should itself be a Pair


# FOR TWEAKING
LOG_INTERVAL = .5
LOGFILE_DIR = "logs"
ENABLE_PISTON = Pair(True, False)  # e.g. only use left crusher for testing
REST_N_FROM_TOP = 1500

STEP_DELAY = .0004  # Delay between setting pin high and low when pulsing the stepper motors
TIGHT_LOOP_INTERVAL = .0001  # delay after running each iteration of the tracking loop

ALLOWABLE_DISCREPANCY = 20  # delta between sensor reading and target which triggers a movement
TWO_KG = Pair(0.413, 0.443)  # sensor readings at 2kg load - these need to be measured!!!
DASHBOARD_UPDATE_INTERVAL = .2
SERVER_PORT = 2008




# PROBABLY BEST LEFT

STEP_PIN = Pair(2, 3)
DIRECTION_PIN = Pair(6, 7)
HIGH_LIMIT_PIN = Pair(14, 15)
SENSOR_PIN = Pair(4, 5)  # note these are the analog pins

UP = 0  # specify direction of rotation
DOWN = 1
MOVEMENT_LABELS = {UP: 'up', DOWN: 'down'}
MOVEMENT = {v: k for k, v in MOVEMENT_LABELS.items()}
STEPS_PER_FULL_STEP = 8  # We use micro stepping, so 8 pulses per full step of the motor
FULL_STEPS_PER_REV = 200
STEPS_PER_REV = FULL_STEPS_PER_REV * STEPS_PER_FULL_STEP
MM_PER_REV = 5  # 5mm of travel per revolution of the motor shaft
MM_MAX_TRAVEL = 25  # We don't want the motors to move more than this number of mm
MAX_STEPS = (MM_MAX_TRAVEL / MM_PER_REV) * STEPS_PER_REV
