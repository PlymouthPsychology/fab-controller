from functools import partial
import os
import random
import csv
from tempfile import TemporaryFile
from datetime import datetime
from collections import namedtuple, deque
import json
import gevent
from gevent.pywsgi import WSGIServer
import gevent.monkey
from flask import Flask, Response, redirect
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

# use a deque for the raw sensor readings for speed, store the last 50
app.measurements = {'left': deque(maxlen=50), 'right': deque(maxlen=50)}
app.smoothed = {'left': 0, 'right': 0}

app.blocks = deque()

app.programme_countdown = None

# HELPER FUNCTIONS


def stopall():
    [i.kill() for i in app.blocks]
    app.blocks.clear()
    _set_block_targets(0, 0)
    app.programme_countdown = None


def _set_block_targets(left, right):
    """Function used by spawn_later to set target forces."""
    d = {'left': left, 'right': right, "timestamp": datetime.now()}
    app.targets.update({'left': left, 'right': right, "timestamp": datetime.now()})
    socketio.emit('actionlog', "Setting L={}, R={}".format(left, right))


Block = namedtuple('Block', ['duration', 'l', 'r'])


def _validate_json_program(jsondata):
    istriple = lambda i: len(i) == 3
    try:
        prog = json.loads(jsondata['data'])
        mkblock = lambda i: isinstance(i, dict) and Block(**i) or Block(*i)
        prog = [mkblock(i) for i in prog]
        return prog

    except Exception, e:
        emit('actionlog', "Program error: " + str(e), broadcast=True)
        return False


def _log_action(msg):
    socketio.emit('actionlog', msg)
    app.logfile.write(str(msg) + "\n")


def _schedule_program_for_execution(prog):
    # clear everything from the queue
    stopall()

    # work through the program, spawning future targets
    cumtime = 0
    for block in prog:
        app.blocks.append(gevent.spawn_later(cumtime, _set_block_targets, *(block.l, block.r)))
        cumtime = cumtime + block.duration

    app.programme_countdown = cumtime
    # make sure we end up back at a target of zero
    app.blocks.append(gevent.spawn_later(cumtime, _set_block_targets, *(0, 0)))
    app.blocks.append(gevent.spawn_later(cumtime, _log_action, *("Program complete",)))


# WEBSOCKET ROUTES
@socketio.on('clear_log')
def clear_log(message):
    makefreshlog()
    emit('log', "Logfile cleared.", broadcast=True)


@socketio.on('set_manual')
def set_manual(forces):
    _set_block_targets(forces['left'], forces['right'])


@socketio.on('log')
def log_actions(message):
    _log_action(str(message))


@socketio.on('stopall')
def stop_everything(json):
    stopall()


@socketio.on('new_program')
def run_program_from_json(jsondata):
    prog = _validate_json_program(jsondata)
    if prog:
        emit('log', "Starting new program", broadcast=True)
        _schedule_program_for_execution(prog)


# REGULAR HTTP ROUTES


@app.route('/')
def hello():
    return redirect("/index.html", code=302)


@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)


@app.route('/log/', methods=['GET'])
def download_log():
    app.logfile.seek(0)
    out = app.logfile.readlines()
    return Response(out, mimetype='text/event-stream')


# BACKGROUND TASKS/HARDWARE CONTROL CODE IS BELOW

def programme_countdown():
    while True:
        if app.programme_countdown is not None:
            socketio.emit('countdown', {'remaining': app.programme_countdown})

            if app.programme_countdown == 0:
                app.programme_countdown = None

            if app.programme_countdown > 0:
                app.programme_countdown = app.programme_countdown - 1

        gevent.sleep(1)


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
    dirpin = MOTORS[motor]['direction']

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
    app.logfile = TemporaryFile(mode="r+")
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
        'remaining': app.programme_countdown,
    })


def update_dash():
    while 1:
        socketio.emit('update_dash', {'data': _dashdata()})
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
        gevent.spawn(programme_countdown),
        socketio.run(app)
    ])
