# MOTORS

MOTOR_PINS = {
    'left': {'step': 1, 'direction': 2, 'kill': 11},
    'right': {'step': 3, 'direction': 4, 'kill': 12}
}

SENSOR_PINS = {
    'left': 5, 'right': 6,
}

# specify where CW is high or low when running motors
UP = 1
DOWN = 0

STEPS_PER_FULL_STEP = 8
FULL_STEPS_PER_REV = 200
STEPS_PER_REV = FULL_STEPS_PER_REV * STEPS_PER_FULL_STEP
MM_PER_REV = 5
MM_MAX_TRAVEL = 20
MAX_STEPS = (MM_MAX_TRAVEL / MM_PER_REV) * STEPS_PER_REV

LOAD_CELL_INPUT_RANGE = (0, 4096)
MOTOR_STEP_RANGE = (0, MAX_STEPS)

ALLOWABLE_DISCREPANCY = .5  # delta between sensor reading and target which triggers a movement


# SENSORS

SMOOTHING_WINDOW = 10
SENSOR_POLL_INTERVAL = .01  # too cpu intensive if less than this?
SENSOR_SMOOTHED_CALC_INTERVAL = .04


# CLIENT

LOG_INTERVAL = 1  # seconds
DASHBOARD_UPDATE_INTERVAL = .1






