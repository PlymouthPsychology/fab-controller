import signal
import sys
from collections import deque
from datetime import datetime
import re
from flask import Flask, Response, redirect
from flask.ext.socketio import SocketIO, send, emit
from getarduino import get_board
import gevent
from pain_logging import *
from settings import *

print "Configuring flask app"
app = Flask(__name__, )
app.config['debug'] = False
socketio = SocketIO(app)
app.blocks = deque()
app.programme_countdown = None


print "Acquiring the arduino board and starting iterator..."
board, boarditerator = get_board()
gevent.sleep(.2)


# this is IMPORTANT!!
# if not fired the board will need to be unplgged and plugged in again
def signal_handler(signal, frame):
    print('You pressed Ctrl+C! Cleaning up...')
    board.exit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


print "Setting up pins"
live_pins = {
    'left': {
        'limit_top_pin': board.get_pin('d:{}:i'.format(HIGH_LIMIT_PIN.left)),
        'sensor_pin': board.get_pin('a:{}:i'.format(SENSOR_PIN.left)),
        'step_pin': board.get_pin('d:{}:o'.format(STEP_PIN.left)),
        'direction_pin': board.get_pin('d:{}:o'.format(DIRECTION_PIN.left)),
    },
    'right': {
        'limit_top_pin': board.get_pin('d:{}:i'.format(HIGH_LIMIT_PIN.right)),
        'sensor_pin': board.get_pin('a:{}:i'.format(SENSOR_PIN.right)),
        'step_pin': board.get_pin('d:{}:o'.format(STEP_PIN.right)),
        'direction_pin': board.get_pin('d:{}:o'.format(DIRECTION_PIN.right)),
    }
}

gevent.sleep(.5)


print "Checking sensors...",
while True:
    if live_pins['left']['sensor_pin'].read() and live_pins['right']['sensor_pin'].read():
        print "found sensors."
        break

print "Checking switches...",
while True:
    l, r = live_pins['left']['limit_top_pin'].read(), live_pins['right']['limit_top_pin'].read()
    if l is not None and r is not None:  # test for not None because switch could be false at startup
        print "found top limit switches."
        break


# scale a value in range (a,b) to corresponding value in range (c,d)
scale_range = lambda x, OldMin, OldMax, NewMin, NewMax: \
    (((x - OldMin) * (NewMax - NewMin)) / (OldMax - OldMin)) + NewMin

class Crusher(object):
    """Manages a finger crusher, including sensor, motor and limit switches."""

    direction = None
    steps_from_top = 0  # note this may not be correct on switch on, but we will initialise by driving to top
    target = None

    def __init__(self, zero, twokg, name="leftorright"):

        self.target = 0  # target weight for this crusher in grams
        self.direction = UP  # default to going up
        self.name = name
        self.zero = zero  # zero set by reading the sensors when creating instance
        self.twokg = twokg  # voltage reading when 2kg applied to sensor

    def set_direction(self, direction):
        if self.direction != direction:
            print "Setting", self.name, MOVEMENT_LABELS[direction]
            live_pins[self.name]['direction_pin'].write(direction)
            self.direction = direction

    def at_top(self):
        # note we use bool(not not self.limit_top_pin.read()) because
        # switch logic is reversed (normally high, pulled low when switch is
        # depressed)
        return bool(not live_pins[self.name]['limit_top_pin'].read())

    def go_to_top_and_init(self):

        print "Moving", self.name, "to top to initialise."
        self.set_direction(UP)

        _i = 0
        while self.pulse() > 0:  # pulse returns the number of steps moved
            # sys.stdout.write("\r{} pulses up".format(_i))
            _i += 1
            # sys.stdout.flush()

        print "\n", self.name, "is at top limit switch."
        self.set_direction(DOWN)
        self.pulse(1500)
        print self.name, "is ready"
        self.steps_from_top = 0

    def pulse(self, n=1):
        """Pulse the stepper motor if safe to do so. Return error code or
        number of steps.

        -1 = At top
        -2 = At bottom
        """

        if self.direction is DOWN and self.steps_from_top >= (MAX_STEPS - n):
            # print self.name, "too low to step. Now at ", self.steps_from_top, "Need to step ", n
            return -2

            # don't go within 100 steps of the top
        if self.direction is UP and self.at_top():
            # print self.name, "too high to step. Now at ", self.steps_from_top, "Need to step ", n
            return -1

        p = live_pins[self.name]['step_pin']
        for i in range(n):
            p.write(1)
            gevent.sleep(STEP_DELAY)
            p.write(0)
            gevent.sleep(STEP_DELAY)

        if self.direction == DOWN:
            self.steps_from_top += n
        else:
            self.steps_from_top += - n

        return n

    def analog_reading(self):
        """Not actually volts - just the input from the analog input"""
        return live_pins[self.name]['sensor_pin'].read()

    def zero_sensor(self):
        self.zero = self.analog_reading()
        print "Setting zero point for", self.name, "to analog reading:{}".format(self.zero)

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
        nsamples = 6  # number of weight samples to take
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
    print (l, r)


@socketio.on('new_program')
def run_program_from_json(jsondata):
    prog = validate_json_program(jsondata)
    if prog:
        print prog
        schedule_program_for_execution(prog)


@socketio.on('stopall')
def stop_everything(x):
    stopall()
    print "Stopping everything"


@socketio.on('restonfingers')
def restonfingers(x):
    app.left.target = 20
    app.right.target = 20
    print "Resting on fingers"


@socketio.on('zero_sensor')
def zero_sensors(x):
    app.left.zero_sensor()
    app.right.zero_sensor()
    print "Zero'd both sensors"


@socketio.on('lift_slightly')
def lift_slightly(x):
    app.left.set_direction(UP)
    app.left.pulse(n=300)
    app.left.set_direction(UP)
    app.left.pulse(n=300)
    print "Lifted both pistons slightly."


def log_action(msg):
    print msg
    socketio.emit('log', {'message': msg})


def stopall():
    [i.kill() for i in app.blocks]
    app.blocks.clear()
    set_block_targets(Pair(0, 0))
    app.programme_countdown = None
    socketio.emit('log', {'message': "Stopping"})


def validate_json_program(jsondata):

    lines = [x for x in jsondata['data'].splitlines() if x.strip()]
    lines = [x for x in lines if x[0] is not "#"]
    lines = [re.split('\W+|[,]', i) for i in lines]
    prog = [map(int, i) for i in lines]

    try:
        mkblock = lambda i: Block(i[0], Pair(i[1], i[2]))
        blocks = [mkblock(i) for i in prog]
        msg = "Program validated"
        print msg
        # emit('actionlog', msg, broadcast=True)
        # socketio.emit('log', {'message': msg})
        print map(type, blocks)
        return blocks

    except Exception, e:
        msg = "Program error: " + str(e)
        print msg
        emit('actionlog', msg, broadcast=True)
        socketio.emit('log', {'message': msg})
        return False


def schedule_program_for_execution(prog):

    stopall()  # clear everything already in the queue

    # work through the program, spawning functiosn which will set future target values
    cumtime = 0
    for block in prog:
        app.blocks.append(gevent.spawn_later(cumtime, set_block_targets, *(block.grams, )))
        cumtime += block.duration

    app.programme_countdown = cumtime  # se the countdown timer

    # make sure we return to a target of zero
    app.blocks.append(gevent.spawn_later(cumtime, set_block_targets, Pair(0, 0)))
    app.blocks.append(gevent.spawn_later(cumtime, log_action, *("Program complete",)))


def set_block_targets(grams):
    """Function used by spawn_later to set target forces."""

    app.left.target = grams.left
    app.right.target = grams.right
    msg = "Setting L={}, R={}".format(grams.left, grams.right)
    socketio.emit('log', {'message': msg})
    print(msg)


def log_data():
    """Log every LOG_INTERVAL to a text file."""
    while True:
        socketio.emit('log', _build_log_entry())
        gevent.sleep(LOG_INTERVAL)


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
        socketio.emit('update_dash', {'data': make_dashdata(app)})
        gevent.sleep(DASHBOARD_UPDATE_INTERVAL)


def tight():
    while 1:
        ENABLE_PISTON.left and app.left.track()
        ENABLE_PISTON.right and app.right.track()
        gevent.sleep(.0001)


if __name__ == "__main__":

    # test the left machine
    print "Starting crusher instances:",

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
        ENABLE_PISTON.left and gevent.spawn(app.left.go_to_top_and_init),
        ENABLE_PISTON.right and gevent.spawn(app.right.go_to_top_and_init),
        gevent.spawn(tight),
        gevent.spawn(update_dash),
        gevent.spawn(programme_countdown),
        socketio.run(app, host="0.0.0.0", port=SERVER_PORT)
    ])
