#!/usr/bin/env python

import webbrowser
from collections import deque
from datetime import datetime
import os
import re
import signal
import sys

from flask import Flask, Response, redirect
from flask_socketio import SocketIO, send, emit
from _getarduino import get_board
import gevent
from _pain_logging import *
from settings import *

print("Configuring flask app")
app = Flask(__name__, )
app.config['debug'] = False
socketio = SocketIO(app)
app.blocks = deque()
app.programme_countdown = None
app.logfilename = "log.txt"


print("Acquiring the arduino board and starting iterator...")
board, boarditerator = get_board()


# THIS IS IMPORTANT!!
# If board.exit() not fired the board will need to be unplgged and 
# plugged in again to work correctly.
def signal_handler(signal, frame):
    print('You pressed Ctrl+C! Cleaning up...')
    board.exit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


print("Setting up pins")
live_pins = {
    'left': {
        'high_limit_pin': board.get_pin('d:{}:i'.format(HIGH_LIMIT_PIN.left)),
        'low_limit_pin': board.get_pin('d:{}:i'.format(LOW_LIMIT_PIN.left)),
        'sensor_pin': board.get_pin('a:{}:i'.format(SENSOR_PIN.left)),
        'step_pin': board.get_pin('d:{}:o'.format(STEP_PIN.left)),
        'direction_pin': board.get_pin('d:{}:o'.format(DIRECTION_PIN.left)),
    },
    'right': {
        'high_limit_pin': board.get_pin('d:{}:i'.format(HIGH_LIMIT_PIN.right)),
        'low_limit_pin': board.get_pin('d:{}:i'.format(LOW_LIMIT_PIN.right)),
        'sensor_pin': board.get_pin('a:{}:i'.format(SENSOR_PIN.right)),
        'step_pin': board.get_pin('d:{}:o'.format(STEP_PIN.right)),
        'direction_pin': board.get_pin('d:{}:o'.format(DIRECTION_PIN.right)),
    }
}


led = board.get_pin('d:13:o')


def flash():
    print("flash!", end=' ')
    led.write(1)
    gevent.sleep(.1)
    led.write(0)
    gevent.sleep(.1)


live_pins['left']['sensor_pin'].enable_reporting()
live_pins['right']['sensor_pin'].enable_reporting()


print("Checking switches...")
[flash() for i in range(10)]

while True:
    gevent.sleep(.1)
    l, r = live_pins['left']['high_limit_pin'].read(), live_pins['right']['high_limit_pin'].read()
    if l is not None and r is not None:  # test for not None because switch could be false at startup
        print("found top limit switches.")
        print("left is", l)
        print("right is", r)
        break

while True:
    gevent.sleep(.1)
    l, r = live_pins['left']['low_limit_pin'].read(), live_pins['right']['low_limit_pin'].read()
    if l is not None and r is not None:  # test for not None because switch could be false at startup
        print("found bottom limit switches.")
        print("left is", l)
        print("right is", r)
        break


print("Checking sensors...", end=' ')
while True:
    gevent.sleep(.1)
    if live_pins['left']['sensor_pin'].read() and live_pins['right']['sensor_pin'].read():
        print("found sensors.")
        break


# scale a value in range (a,b) to corresponding value in range (c,d)
scale_range = lambda x, OldMin, OldMax, NewMin, NewMax: \
    (((x - OldMin) * (NewMax - NewMin)) / (OldMax - OldMin)) + NewMin


class Crusher(object):
    """Manages a finger crusher, including sensor, motor and limit switches."""

    direction = None
    steps_from_top = 3000  # note this may not be correct on switch on, but we will initialise by driving to top
    target = None

    def __init__(self, zero, twokg, name="leftorright"):

        self.tracking = True
        self.target = 0  # target weight for this crusher in grams
        self.direction = UP  # default to going up
        self.name = name
        self.zero = zero  # zero set by reading the sensors when creating instance
        self.twokg = twokg  # voltage reading when 2kg applied to sensor

        self._top_switch_gen = self._switch_state_generator("top")
        self._bottom_switch_gen = self._switch_state_generator("bottom")
        self.at_top = next(self._top_switch_gen)
        self.at_bottom = next(self._bottom_switch_gen)

    def update_switch_states(self):
        self.at_top = next(self._top_switch_gen)

    def set_direction(self, direction):
        if self.direction != direction:
            live_pins[self.name]['direction_pin'].write(direction)
            self.direction = direction

    def _switch_state_generator(self, position):
            """Introduce min delay in readings and hysteresis for change in state"""

            if position == "top":
                pin = live_pins[self.name]['high_limit_pin']
            else:
                pin = live_pins[self.name]['low_limit_pin']

            windowlen = SWITCH_CHECKING_WINDOW_LENGTH
            window = deque(maxlen=windowlen)
            window.extend([True] * windowlen)
            state = True

            while True:
                window.append(not pin.read())  # reverse here

                # note, we don't always *change* state...
                if all(window):
                    state = True

                elif not any(window):
                    state = False

                yield state


    def go_to_top(self):
        self.set_direction(UP)
        gevent.sleep(.1)

        while True:
            self.update_switch_states()
            if self.pulse() < 1:
                break
            gevent.sleep(0)


    def go_to_top_and_init(self):

        print("Moving down slightly")
        self.set_direction(DOWN)
        gevent.sleep(.1)
        self.pulse(n=100)

        print("Moving", self.name, "to top to initialise.")
        self.go_to_top()

        self.steps_from_top = 0
        print("\n", self.name, "is at top limit switch.")

        self.set_direction(DOWN)
        gevent.sleep(.1)
        for i in range(REST_N_FROM_TOP):
            self.pulse()
            gevent.sleep(0)

        print("\n", self.name, "is ready")



    def pulse(self, n=1):
        """Pulse the stepper motor if safe to do so. Return error code or
        number of steps.

        -1 = At top
        -2 = At bottom
        """

        if self.direction is DOWN and self.steps_from_top >= (MAX_STEPS - n) and not self.at_bottom:
            print(self.name, "too low to step. Now at ", self.steps_from_top, "Need to step ", n)
            return -2

        # don't go within 100 steps of the top
        if self.direction is UP:
            if self.steps_from_top < 100 or self.at_top:
                print(self.name, "too high to step. Now at ", self.steps_from_top, ". At-top=", self.at_top, ". Need to step ", n)
                if self.at_top:  # reset the counter
                    self.steps_from_top = 0
                return -1

        # do the stepping
        p = live_pins[self.name]['step_pin']
        for i in range(n):
            p.write(1)
            gevent.sleep(STEP_DELAY)
            p.write(0)
            gevent.sleep(STEP_DELAY)

        # update the internal step counter
        if self.direction == DOWN:
            self.steps_from_top += n
        else:
            self.steps_from_top += -n
        
        # print self.name, n, self.steps_from_top, self.at_top, self.direction
        return n

    def analog_reading(self):
        """Not actually volts - just the input from the analog input"""
        return live_pins[self.name]['sensor_pin'].read()

    def zero_sensor(self):
        self.zero = self.analog_reading()
        msg = "Setting zero point for {} to analog reading: {}".format(self.name, self.zero)
        print(msg)

    def grams(self):
        """Scale using parameters in settings. Note parameters for each hand/sensor may differ."""
        g = scale_range(self.analog_reading(), self.zero, self.twokg, 0, 2000)
        return max([g, 0])

    def update_direction(self, delta):
        # decide which direction
        d = delta > 0 and DOWN or UP
        self.set_direction(d)

    def track(self):
        """Pulse and change direction to track target weight."""
        self.update_switch_states()

        if not self.tracking:
            return

        nsamples = SENSOR_MEASUREMENTS_WINDOW_LENGTH
        margin = max([ALLOWABLE_DISCREPANCY, self.target * .05])
        delta = self.target - (sum(self.grams() for i in range(nsamples)) / nsamples)
        adelta = abs(delta) + 1
        if adelta > margin:
            self.update_direction(delta)
            self.pulse()


@app.route('/')
def hello():
    return redirect("/index.html", code=302)


@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)


@socketio.on('set_manual')
def set_manual(forces):
    l, r = (forces['left'], forces['right'])
    app.left.target = l
    app.right.target = r
    _log_session_data({'targets': Pair(l, r)})


@socketio.on('new_program')
def run_program_from_json(jsondata):
    prog = validate_json_program(jsondata)
    if prog:
        _log_session_data({'programme': prog})
        schedule_program_for_execution(prog)


@socketio.on('stopall')
def stop_everything(x):
    stopall()


@socketio.on('set_logfile_name')
def set_logfile_name(data):
    app.logfilename = data.get("logfilename", "log.txt")
    print("Updated logfilename to ", app.logfilename)


def _log_session_data(data):
    """Write a dictionary as a string to a line in the logfile."""
    if not isinstance(data, dict):
        data = {'message': data}

    data.update({'timestamp': datetime.now()})
    with open(os.path.join(LOGFILE_DIR, app.logfilename), "a") as f:
        f.write(str(data) + "\n")
    if data.get('message', None):
        # print data.get('message')
        socketio.emit('log', data)
    else:
        pass
        # print "Wrote to log: ", str(data)


@socketio.on('log_session_data')
def log_session_data(data):
    """Socket handler to write to log from client."""
    return _log_session_data(data)


@socketio.on('restonfingers')
def restonfingers(x):
    app.left.target = 20
    app.right.target = 20
    _log_session_data({'message': "Resting on fingers"})


@socketio.on('toggle_tracking')
def toggle_tracking(x):
    app.left.tracking = not app.left.tracking
    app.right.tracking = not app.right.tracking
    print("Toggled tracking to:", app.left.tracking, app.right.tracking)



@socketio.on('zero_sensor')
def zero_sensors(x):
    app.left.zero_sensor()
    app.right.zero_sensor()
    print("Zero'd both sensors")


@socketio.on('mark_twokg')
def mark_twokg(data):
    crusher = getattr(app, data['hand'])
    crusher.twokg = crusher.analog_reading()
    print("Set 2kg value for {} to {}".format(crusher.name, crusher.twokg))


@socketio.on('lift_slightly')
def lift_slightly(x):
    app.left.set_direction(UP)
    app.left.pulse(n=300)
    app.left.set_direction(UP)
    app.left.pulse(n=300)
    print("Lifted both pistons slightly.")


@socketio.on('manual_pulse')
def manual_pulse(data):
    print("Executing manual pulses", str(data))
    crusher = getattr(app, data['hand'])
    crusher.set_direction(MOVEMENT[data['direction'].lower()])
    crusher.pulse(n=int(data['n']))


def stopall():
    _log_session_data({'message': "Stop button pressed."})
    [i.kill() for i in app.blocks]
    app.blocks.clear()
    set_block_targets(Pair(0, 0))
    app.left.go_to_top()
    app.right.go_to_top()
    app.programme_countdown = None


def validate_json_program(jsondata):

    try:
        lines = [x for x in jsondata['data'].splitlines() if x.strip()]  # strip whitespace
        lines = [x for x in lines if x[0] is not "#"]  # remove comments
        lines = [re.split('\W+|[,]', i) for i in lines]  # split duration, left, right
        prog_ints = [list(map(int, i)) for i in lines]  # we need integers
        return [Block(x[0], Pair(x[1], x[2])) for x in prog_ints]  # return blocks

    except Exception as e:
        msg = "Program error: " + str(e)
        print(msg)
        emit('actionlog', msg, broadcast=True)
        return False


def schedule_program_for_execution(prog):

    stopall()  # clear everything already in the queue
    prog = deque(prog)  # because we want to popleft on this

    def add_blocks_keeping_running_time(programme, blocks, cumtime):
        """Recursive function to spawn a list of future blocks from a user program.

        Return tuple of the blocks and the total running time of the programme.
        """
        if not programme:
            print("finished building blocks from prog")
            blocks.append(gevent.spawn_later(cumtime, set_block_targets, Pair(0, 0)))
            blocks.append(gevent.spawn_later(cumtime, _log_session_data, *({'message': "Program complete"})))
            return (blocks, cumtime)
        else:
            block = programme.popleft()
            blocks.append(gevent.spawn_later(cumtime, set_block_targets, *(block.grams, )))
            return add_blocks_keeping_running_time(programme, blocks, cumtime + block.duration)

    app.blocks, app.programme_countdown = add_blocks_keeping_running_time(prog, deque(), 0)
    print(app.blocks, app.programme_countdown)


def set_block_targets(grams):
    """Function used by spawn_later to set target forces."""

    app.left.target, app.right.target = grams
    msg = "Setting L={}, R={}".format(*grams)
    _log_session_data({"targets": grams})




# THE LOOPS JOINED BY GEVENT

def programme_countdown():
    while True:
        if app.programme_countdown is not None:
            socketio.emit('countdown', {'remaining': app.programme_countdown})
            if app.programme_countdown == 0:
                app.programme_countdown = None
            if app.programme_countdown > 0:
                app.programme_countdown += -1

        gevent.sleep(1)


def update_dash():
    while 1:
        data = make_dashdata(app)
        socketio.emit('update_dash', {'data': data})
        gevent.sleep(DASHBOARD_UPDATE_INTERVAL)

def tight():
    while 1:
        ENABLE_PISTON.left and app.left.track()
        ENABLE_PISTON.right and app.right.track()
        gevent.sleep(TIGHT_LOOP_INTERVAL)


def init_crushers():
    ENABLE_PISTON.left and app.left.go_to_top_and_init()
    ENABLE_PISTON.right and app.right.go_to_top_and_init()
    print("Opening browser window")
    c = webbrowser.get('safari')
    c.open("127.0.0.1:{}".format(SERVER_PORT), new=0, autoraise=True)


def log_sensors():
    while 1:
        if app.left.target > 0 or app.right.target > 0:
            _log_session_data({
                'measurement': Pair(app.left.grams(), app.right.grams()),
                'targets': Pair(app.left.target, app.right.target),
            })

        gevent.sleep(LOG_INTERVAL)


if __name__ == "__main__":

    # test the left machine
    print("Starting crusher instances:")

    app.left = Crusher(
        live_pins['left']['sensor_pin'].read(),
        TWO_KG.left,
        "left"
    )
    app.right = Crusher(
        live_pins['right']['sensor_pin'].read(),
        TWO_KG.right,
        "right"
    )
    
    gevent.joinall([
        # only run the piston if enabled in settings
        gevent.spawn(init_crushers),
        gevent.spawn(tight),
        gevent.spawn(log_sensors),
        gevent.spawn(update_dash),
        gevent.spawn(programme_countdown),
        socketio.run(app, host="0.0.0.0", port=SERVER_PORT)
    ])