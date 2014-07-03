from functools import partial
import os
import random
import csv
from tempfile import SpooledTemporaryFile
from datetime import datetime
from collections import namedtuple, deque
import json
import gevent
from gevent.pywsgi import WSGIServer
import gevent.monkey
from flask import Flask, Response
from flask.ext.socketio import SocketIO, send, emit
gevent.monkey.patch_all()


LOG_INTERVAL = 1  # seconds
MOTOR_INTERVAL = .01
SENSOR_POLL_INTERVAL = .1
SENSOR_SMOOTHED_CALC_INTERVAL = .2
DASHBOARD_UPDATE_INTERVAL = .1


# specify where CW is high or low when running motors
UP = 0
DOWN = 1

#specify the motor pins
MOTORS = {
    'left': {'step': 1, 'direction': 2},
    'right': {'step': 3, 'direction': 4}
}



# Flask allows us to define urls and functions for the web interface
app = Flask(__name__, )
app.debug = True

# SocketIO allows web sockets (persistent connections)
socketio = SocketIO(app)


# Specify some 'global' variables
app.targets = {'left': 0, 'right': 0, 'timestamp': datetime.now()}

# use a deque for the raw sensor readings for speed, store the last 100
app.measurements = {'left': deque(maxlen=100), 'right': deque(maxlen=100)}
app.smoothed = {'left': 0, 'right': 0}

app.blocks = deque()



@socketio.on('clear_log')
def clear_log(message):
    makefreshlog()
    emit('log', "Logfile cleared.", broadcast=True)


@socketio.on('blockchange')
def echo_socket(message):
    while True:
        send(message, broadcast=True)


@socketio.on('stopall')
def stopall(json):
    stopall()
    emit('log', "Stopping", broadcast=True)

def stopall():
    [i.kill() for i in app.blocks]
    app.blocks.clear()
    _set_block_targets(0, 0)
    app.targets.update({'left': 0, 'right': 0, "timestamp": datetime.now()})


def _set_block_targets(left, right):
    """Function used by spawn_later to set target forces."""
    d = {'left': left, 'right': right, "timestamp": datetime.now()}
    app.targets.update({'left': left, 'right': right, "timestamp": datetime.now()})
    socketio.emit('log', "Setting L={}, R={}".format(left, right))


@socketio.on('newprog')
def newprog(jsondata):

    # do some checking of prog here
    istriple = lambda i: len(i)==3
    try:
        prog = json.loads(jsondata['data'])
        assert sum(map(istriple, prog))==len(prog), "Program not made of triples."
    except Exception, e:
        emit('log', "Program error: " + str(e), broadcast=True)
        return

    emit('log', "Starting new program", broadcast=True)

    # clear everything from the queue
    stopall()

    # work through the program, spawning future targets
    cumtime = 0
    for duration, left, right in prog:
        app.blocks.append(gevent.spawn_later(cumtime, _set_block_targets, *(left, right)))
        cumtime = cumtime + duration

    # make sure we end up back at a target of zero
    app.blocks.append(gevent.spawn_later(cumtime, _set_block_targets, *(0, 0)))

@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)

@app.route('/log/', methods=['GET'])
def download_log():
    app.logfile.seek(0)
    out = app.logfile.readlines()
    return Response(out, mimetype='text/event-stream')


def run_blocks(prog, methods=['GET']):
    """A generator function to run a specific program of blocks.
    Yields a series of strings describing the progress of the program.

    Programs are lists of Blocks - a namedtuple consisting of a duration
    and a left and right target value.

    TODO - this function should only really accept POST or PUT requests because browsers might cache or repeat GETs
    """

    yield "Starting program\n"
    app.timer = 0
    for duration, left, right in prog:
        app.targets.update({'left': left, 'right': right, "timestamp": datetime.now()})
        infostring = "Setting to: L={}, R={} for {} seconds\n".format(left, right, duration)
        socketio.send(infostring)
        yield infostring
        gevent.sleep(duration)

    stopall()
    yield "Program complete; resetting target forces to zero."




# BACKGROUND TASKS/HARDWARE CONTROL CODE IS BELOW

def poll_sensors():
    """Check the sensor readings and update app state."""
    while True:
        # TODO fix this to get real measures from GPIO
        app.measurements['left'].append(random.random())
        app.measurements['right'].append(random.random())

        gevent.sleep(SENSOR_POLL_INTERVAL)


def smooth_current_sensor_values(func=sum):
    """Calculate the current sensor readings, perhaps using smoothing function."""
    while True:
        app.smoothed.update({'left': func(app.measurements['left']), 'right': func(app.measurements['right']), })
        gevent.sleep(SENSOR_SMOOTHED_CALC_INTERVAL)

digitalWrite = lambda pin, val: None

def _set_direction(motor, direction):
    digitalWrite(MOTORS[motor]['direction'], direction)


def run_motor(motor):
    steppin = MOTORS[motor]['step']
    dirpin =  MOTORS[motor]['direction']

    while True:
        # XXX TODO THIS IS NOT FINISHED
        # delay is the inverse of the difference between target and current
        # which adjusts the speed of the motor
        # we might need to add some scaling factor here
        # might also not want to step if delay is < SOMEVALUE
        # at this point we could also change direction if needed

        digitalWrite(steppin, 1)
        delay = 1 / (app.targets[motor] - app.smoothed[motor]) + 1
        if delay > 0:
            digitalWrite(dirpin, UP)
        else:
            digitalWrite(dirpin, DOWN)
        gevent.sleep(delay)

# make functions for L and R which can be joined independently to the event loop
run_left = partial(run_motor, 'left')
run_right = partial(run_motor, 'right')


def makefreshlog():
    # is this a problem? will we kill the disk eventually... it is a temp file tho...
    app.logfile = SpooledTemporaryFile(mode="wab", max_size=3145728)  # 3mb before rolling to disk
    app.logfile.write("target_L,target_R,smooth_L,smooth_R,timestamp\n")


def log_data():
    """Log every LOG_INTERVAL to a text file."""
    while 1:
        out = "{:8.3g},{:8.3g},{:8.3g},{:8.3g},{}\n".format(
            app.targets['left'],
            app.targets['right'],
            app.smoothed['left'],
            app.smoothed['right'],
            datetime.now(),
            )
        app.logfile.write(out)
        gevent.sleep(LOG_INTERVAL)


def _dashdata():
    return json.dumps({
        'target_L': app.targets['left'],
        'target_R': app.targets['right'],
        'smooth_L': app.smoothed['left'],
        'smooth_R': app.smoothed['right'],
    })

def update_dash():
    while 1:
        socketio.emit('update_dash', {'data': _dashdata() })
        gevent.sleep(DASHBOARD_UPDATE_INTERVAL)

# THIS PART JOINS ALL THE KEY FUNCTIONS INTO THE COOPERATIVE EVENT LOOP

if __name__ == '__main__':
    print("Running...")
    makefreshlog()

    gevent.joinall([
        gevent.spawn(log_data),
        gevent.spawn(poll_sensors),
        gevent.spawn(smooth_current_sensor_values),
        gevent.spawn(run_left),
        gevent.spawn(run_right),
        gevent.spawn(update_dash),
        socketio.run(app)
    ])

