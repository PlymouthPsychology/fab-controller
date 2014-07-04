from functools import partial
import os
import math
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


app = Flask(__name__, )
app.debug = True
socketio = SocketIO(app)



# PAIN MACHINE CONSTANTS

LOG_INTERVAL = 1  # seconds
SENSOR_POLL_INTERVAL = .001  # too cpu intensive if less than this?
SENSOR_SMOOTHED_CALC_INTERVAL = .2
DASHBOARD_UPDATE_INTERVAL = .1

# specify where CW is high or low when running motors
UP = 1
DOWN = 0

#specify the motor pins
MOTORS = {
    'left': {'step': 1, 'direction': 2},
    'right': {'step': 3, 'direction': 4}
}



# Specify some 'global' variables
app.targets = {'left': 0, 'right': 0, 'timestamp': datetime.now()}

# use a deque for the raw sensor readings for speed, store the last 50
SMOOTHING_WINDOW = 30

app.measurements = {'left': deque(maxlen=SMOOTHING_WINDOW), 'right': deque(maxlen=SMOOTHING_WINDOW)}
app.smoothed = {'left': 0, 'right': 0}


app.blocks = deque()

app.programme_countdown = None


ALLOWABLE_DISCREPANCY = .5

# to fake sensor data
app.true_force = {'left': 0, 'right': 0}
app.motor_speed = {'left': 0, 'right': 0}
sensor_noise = lambda: random.random() * .3
STEP_SIZE_AS_FORCE = .025  # how much force each step adds/removes when we fake things

# HELPER FUNCTIONS
def stopall():
    [i.kill() for i in app.blocks]
    app.blocks.clear()
    _set_block_targets(0, 0)
    app.programme_countdown = None
    socketio.emit('log', {'message': "Stopping"})


def _set_block_targets(left, right):
    """Function used by spawn_later to set target forces."""
    d = {'left': left, 'right': right, "timestamp": datetime.now()}
    app.targets.update({'left': left, 'right': right, "timestamp": datetime.now()})
    msg = "Setting L={}, R={}".format(left, right)
    socketio.emit('log', {'message': msg})
    socketio.emit('actionlog', msg)


Block = namedtuple('Block', ['duration', 'l', 'r'])


def _validate_json_program(jsondata):
    istriple = lambda i: len(i) == 3
    try:
        prog = json.loads(jsondata['data'])
        mkblock = lambda i: isinstance(i, dict) and Block(**i) or Block(*i)
        prog = [mkblock(i) for i in prog]
        msg = "Program validated"
        emit('actionlog', msg, broadcast=True)
        socketio.emit('log', {'message': msg})
        return prog

    except Exception, e:
        msg = "Program error: " + str(e)
        emit('actionlog', msg, broadcast=True)
        socketio.emit('log', {'message': msg})
        return False


def _log_action(msg):
    socketio.emit('actionlog', msg)
    socketio.emit('log', {'message': msg})


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
        _schedule_program_for_execution(prog)


# REGULAR HTTP ROUTES

@app.route('/')
def hello():
    return redirect("/index.html", code=302)


@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)


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
        app.measurements['left'].append(app.true_force['left'] + sensor_noise())
        app.measurements['right'].append(app.true_force['right'] + sensor_noise())
        gevent.sleep(SENSOR_POLL_INTERVAL)


_tmp = [1/math.log(i+2) for i in range(SMOOTHING_WINDOW)]
SMOOTHING_CURVE = list(reversed([i/max(_tmp) for i in _tmp]))

smoother = lambda x: sum([i*j for i, j in zip(x, SMOOTHING_CURVE)])/len(x)

def smooth_current_sensor_values(func=smoother):
    """Calculate the current sensor readings, perhaps using smoothing function."""
    while True:
        app.smoothed.update({
            'left': func(app.measurements['left']),
            'right': func(app.measurements['right']),
        })
        gevent.sleep(SENSOR_SMOOTHED_CALC_INTERVAL)

digitalWrite = lambda pin, val: None


def _step_motor(hand):
    digitalWrite(MOTORS[hand]['step'], 1)

    # fake the true forces
    if MOTORS[hand]['direction'] == DOWN:
        app.true_force[hand] = app.true_force[hand] - STEP_SIZE_AS_FORCE
    else:
        app.true_force[hand] = app.true_force[hand] + STEP_SIZE_AS_FORCE



def _set_direction(hand, direction):
    digitalWrite(MOTORS[hand]['direction'], direction)
    MOTORS[hand]['direction'] = direction


def run_motor(hand):
    while True:
        # XXX TODO THIS IS NOT FINISHED
        # delay is the inverse of the difference between target and current
        # which adjusts the speed of the motor
        # we might need to add some scaling factor here
        # might also not want to step if delay is < SOMEVALUE
        # at this point we could also change direction if needed

        # larger delta means we need more force pressing down
        delta =  app.targets[hand] - app.smoothed[hand]
        if abs(delta) > ALLOWABLE_DISCREPANCY:
            # decide which direciton
            if delta > 0:
                _set_direction(hand, UP)
            else:
                _set_direction(hand, DOWN)

            _step_motor(hand)

        delay = (1 / math.log(abs(delta)+2)) / 500
        app.motor_speed[hand] = delay
        gevent.sleep(min([.1, delay]))

# make functions for L and R which can be joined independently to the event loop
run_left = partial(run_motor, 'left')
run_right = partial(run_motor, 'right')


def _build_log_entry():
    return {
        'target_L': app.targets['left'],
        'target_R': app.targets['right'],
        'smooth_L': app.smoothed['left'],
        'smooth_R': app.smoothed['right'],
        'time': datetime.now().isoformat(),
        'remaining': app.programme_countdown,
        'true_L': app.true_force['left'],
        'true_R': app.true_force['right'],
        'motor_speed_L': app.motor_speed['left']*100,
        'motor_speed_R': app.motor_speed['right']*100
    }


def log_data():
    """Log every LOG_INTERVAL to a text file."""
    while True:
        socketio.emit('log', _build_log_entry())
        gevent.sleep(LOG_INTERVAL)


def _dashdata():
    return json.dumps(_build_log_entry())


def update_dash():
    while 1:
        socketio.emit('update_dash', {'data': _dashdata()})
        gevent.sleep(DASHBOARD_UPDATE_INTERVAL)

# THIS PART JOINS ALL THE KEY FUNCTIONS INTO THE COOPERATIVE EVENT LOOP

if __name__ == '__main__':
    print("Running...")

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
