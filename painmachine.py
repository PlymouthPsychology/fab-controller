import json
import re
import math
from datetime import datetime
from collections import deque

import gevent
from gevent.pywsgi import WSGIServer
import gevent.monkey
gevent.monkey.patch_all()

from settings import *
from sensors import av

from flask import Flask
from flask.ext.socketio import SocketIO, send, emit


app = Flask(__name__, )
app.debug = True
socketio = SocketIO(app)


# store each step in a sequence to be run
app.blocks = deque()
app.programme_countdown = None


from ABElectronics_ADCPi import ADCPi
import RPi.GPIO as GPIO
import wiringpi


# Initialise connections to the pi ADC
app.ADC = ADCPi(SENSOR_CHANNEL_CODE.left, SENSOR_CHANNEL_CODE.right, SENSOR_SAMPLE_RATE)

# Register the board with wiringpi
io = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_PINS)

# Also register with GPIO so we can use interrupts
GPIO.setmode(GPIO.BCM)
GPIO.setup(KILL_PIN, GPIO.IN)



class Crusher(object):

    direction = None
    step_delay = STEP_DELAY
    steps_from_top = 0  # note this may not be correct on switch on, but we will initialise by driving to top
    adc = app.ADC
    sensor_channel = None
    target = None
    alpha = None
    beta = None

    def __init__(self, limit_top_pin, step_pin, direction_pin, sensor_channel, alpha, beta, name="crusher"):

        self.target = 0
        self.limit_top_pin = limit_top_pin
        self.name = name
        self.step_pin = step_pin
        self.direction = UP
        self.direction_pin = direction_pin
        self.sensor_channel = sensor_channel
        self.alpha = alpha
        self.beta = beta

        # setup motor pins with wiringpi for speed
        io.pinMode(step_pin, io.OUTPUT)
        io.pinMode(direction_pin, io.OUTPUT)
        io.digitalWrite(direction_pin, UP)

        # setup switch pins with GPIO for interrupts
        GPIO.setup(limit_top_pin, GPIO.IN)

        corrected_alpha = - self.beta * self.volts()
        self.alpha = corrected_alpha
        print "Corrected alpha for ", self.name, corrected_alpha
        print "Completed setup for ", self.name
        print {k: getattr(self, k) for k in dir(self) if not callable(getattr(self, k))}

    def set_direction(self, direction):
        if self.direction != direction:
            print 'updating direction', self.name, direction
            io.digitalWrite(self.direction_pin, direction)
            self.direction = direction

    def at_top(self):
        return GPIO.input(self.limit_top_pin)

    def go_to_top_and_init(self):
        print("Initialising step from top count")
        self.set_direction(UP)
        gevent.sleep()
        print self.name, "going to top"
        while not self.at_top():
            self.pulse(force=True)
            gevent.sleep()
        print self.name, "at top"
        self.steps_from_top = 0


    def pulse(self, n=1, force=False):

            # can override these safety checks
            if not force:
                # don't go beyond MAX_STEPS from the top
                if self.direction is DOWN and self.steps_from_top >= (MAX_STEPS - n):
                    print "too low", self.steps_from_top, n
                    return

                # don't go within 100 steps of the top
                if self.direction is UP and self.steps_from_top < 10:
                    print "too high", self.steps_from_top, n
                    return

            for i in range(n):
                io.digitalWrite(self.step_pin, 1)
                gevent.sleep(self.step_delay)
                io.digitalWrite(self.step_pin, 0)
                gevent.sleep(self.step_delay)

            if self.direction == DOWN:
                self.steps_from_top += n
            else:
                self.steps_from_top += - n



    def volts(self):
        return self.adc.readVoltage(self.sensor_channel)

    def grams(self):
        """Convert using regression parameters in settings.
        Note parameters for each hand/sensor may differ."""
        return self.alpha + self.beta * self.volts()

    def update_direction(self, delta):
        # decide which direction
        d = delta > 0 and DOWN or UP
        self.set_direction(d)



    def track(self):
        """Pulse and change direction to track target weight."""
        while True:
            gevent.sleep(0)
            delta = self.target - self.grams()
            adelta = abs(delta)
            if adelta > ALLOWABLE_DISCREPANCY:
                print "moving", self.name, delta
                npulses = max([1, int(math.log(adelta))])
                gevent.spawn(self.pulse, npulses)
                gevent.spawn(self.update_direction, delta)

            gevent.sleep()

