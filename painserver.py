import json
import re
import math
from datetime import datetime
from collections import deque

import gevent
from gevent.pywsgi import WSGIServer
import gevent.monkey
gevent.monkey.patch_all()

from py_io import read, write, weights
from settings import *


from flask import Flask, Response, redirect
from flask.ext.socketio import SocketIO, send, emit

app = Flask(__name__, )
app.debug = True
socketio = SocketIO(app)



# Specify some 'global' variables

# the desired weight to be applied to each hand
app.targets = Pair(0, 0)

# set the initial direction of travel to be UP
app.direction = Pair(UP, UP)

# use a deque for the raw sensor readings for speed, store the last n values
app.measurements = Pair(deque(maxlen=SMOOTHING_WINDOW), deque(maxlen=SMOOTHING_WINDOW))
app.smoothed = Pair(0, 0)

# store each step in a sequence to be run
app.blocks = deque()
app.programme_countdown = None


try:

    from ABElectronics_ADCPi import ADCPi
    import RPi.GPIO as GPIO

    # Initialise connections to the pi ADC
    app.ADC = ADCPi(SENSOR_CHANNEL_CODE.left, SENSOR_CHANNEL_CODE.right, SENSOR_SAMPLE_RATE)
    app.weight_stream = weight_stream(app.ADC)


    # Register the GPIO pins
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(STEP.left, GPIO.OUT)
    GPIO.setup(STEP.right, GPIO.OUT)
    GPIO.setup(DIRECTION.left, GPIO.OUT)
    GPIO.setup(DIRECTION.right, GPIO.OUT)

    # Initialise pins direction of travel - we start with up...
    write(DIRECTION.left, app.direction.left)
    write(DIRECTION.right, app.direction.right)
except:
    print("No pi available")
    from fakepi import *
    app.ADC = FakeADC()
    GPIO = FakeGPIO()




def poll_sensors():
    """Check the sensor readings and update app state."""
    while True:
        w = weights(app.ADC)
        app.measurements.left.append(w.left)
        app.measurements.right.append(w.right)
        print(w)
        gevent.sleep(SENSOR_POLL_INTERVAL)


# THIS JOINS ALL THE KEY FUNCTIONS INTO THE CO-OPERATIVE EVENT LOOP
if __name__ == '__main__':

    print("Running...")
    gevent.joinall([
        # gevent.spawn(update_dash),
        # gevent.spawn(run_motors_to_top_stop),
        # gevent.spawn(log_data),
        gevent.spawn(poll_sensors),
        # gevent.spawn(smooth_current_sensor_values),
        # gevent.spawn(run_left),
        # gevent.spawn(run_right),
        # gevent.spawn(programme_countdown),
        socketio.run(app)
    ])


