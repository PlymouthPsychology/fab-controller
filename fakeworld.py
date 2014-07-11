import random

# to fake sensor data
def sensor_noise():
    return random.random() * .5

steps_from_top = {'left': 0, 'right': 0}

pin_states = {i:0 for i in range(12)}