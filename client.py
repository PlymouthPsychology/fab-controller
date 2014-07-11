import re
from collections import namedtuple
from datetime import datetime
from flask import Flask, Response, redirect
from flask.ext.socketio import SocketIO, send, emit
import gevent
import json

app = Flask(__name__, )
app.debug = True
socketio = SocketIO(app)

from fakeworld import steps_from_top
from motors import run_motors_to_top_stop
from settings import *

# WEB SOCKET EVENT HANDLERS


def log_action(msg):
    socketio.emit('actionlog', msg)
    socketio.emit('log', {'message': msg})


@socketio.on('set_manual')
def set_manual(forces):
    set_block_targets(forces['left'], forces['right'])


@socketio.on('log')
def log_actions(message):
    log_action(str(message))


@socketio.on('stopall')
def stop_everything(json):
    stopall()


@socketio.on('new_program')
def run_program_from_json(jsondata):
    prog = validate_json_program(jsondata)
    if prog:
        schedule_program_for_execution(prog)



# REGULAR HTTP ROUTES

@app.route('/')
def hello():
    return redirect("/index.html", code=302)


@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)



def stopall():
    [i.kill() for i in app.blocks]
    app.blocks.clear()
    set_block_targets(0, 0)
    app.programme_countdown = None
    socketio.emit('log', {'message': "Stopping"})
    run_motors_to_top_stop()



def schedule_program_for_execution(prog):
    # clear everything from the queue
    stopall()

    # work through the program, spawning future targets
    cumtime = 0
    for block in prog:
        app.blocks.append(gevent.spawn_later(cumtime, set_block_targets, *(block.l, block.r)))
        cumtime = cumtime + block.duration

    app.programme_countdown = cumtime
    # make sure we end up back at a target of zero
    app.blocks.append(gevent.spawn_later(cumtime, set_block_targets, *(0, 0)))
    app.blocks.append(gevent.spawn_later(cumtime, log_action, *("Program complete",)))


def set_block_targets(left, right):
    """Function used by spawn_later to set target forces."""
    d = {'left': left, 'right': right, "timestamp": datetime.now()}
    app.targets.update({'left': left, 'right': right, "timestamp": datetime.now()})
    msg = "Setting L={}, R={}".format(left, right)
    socketio.emit('log', {'message': msg})
    socketio.emit('actionlog', msg)


Block = namedtuple('Block', ['duration', 'l', 'r'])

def validate_json_program(jsondata):

    try:
        prog = json.loads(jsondata['data'])
    except ValueError:
        lines = [x for x in jsondata['data'].splitlines() if x.strip()]
        lines = [x for x in lines if x[0] is not "#"]
        lines = [re.split('\W+|[,]', i) for i in lines]
        print lines
        prog =  [map(float, i) for i in lines]
        
    try:
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


def _build_log_entry():
    return {
        'target_L': app.targets['left'],
        'target_R': app.targets['right'],
        'smooth_L': app.smoothed['left'],
        'smooth_R': app.smoothed['right'],
        'time': datetime.now().isoformat(),
        'remaining': app.programme_countdown and int(app.programme_countdown) or None,
        'true_L': steps_from_top['left'],
        'true_R': steps_from_top['right'],
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


def programme_countdown():
    while True:
        if app.programme_countdown is not None:
            socketio.emit('countdown', {'remaining': app.programme_countdown})

            if app.programme_countdown == 0:
                app.programme_countdown = None

            if app.programme_countdown > 0:
                app.programme_countdown = app.programme_countdown - 1

        gevent.sleep(1)
