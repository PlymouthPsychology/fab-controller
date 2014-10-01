import re
from painmachine import app, socketio, Crusher, io
import gevent
import gevent.monkey
gevent.monkey.patch_all()
from settings import *
from flask import Flask, Response, redirect
from flask.ext.socketio import SocketIO, send, emit
from pain_logging import *


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
    # clear everything from the queue
    stopall()

    # work through the program, spawning future targets
    cumtime = 0
    print map(type, prog)

    for block in prog:
        app.blocks.append(gevent.spawn_later(cumtime, set_block_targets, *(block.grams, )))
        cumtime += block.duration

    print "total time", cumtime
    app.programme_countdown = cumtime
    # make sure we end up back at a target of zero
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
                app.programme_countdown +=  - 1

        gevent.sleep(1)


def update_dash():
    while 1:
        socketio.emit('update_dash', {'data': make_dashdata(app)})
        gevent.sleep(DASHBOARD_UPDATE_INTERVAL)


def tight():
    while 1:
        app.left.track()
        app.right.track()
        gevent.sleep(.000001)


if __name__ == "__main__":

    app.left = Crusher(
        HIGH_LIMIT_PIN.left,
        STEP_PIN.left,
        DIRECTION_PIN.left,
        1,
        BETA.left,
        "left"
    )
    app.right = Crusher(
        HIGH_LIMIT_PIN.right,
        STEP_PIN.right,
        DIRECTION_PIN.right,
        2,
        BETA.right,
        "right"
    )

    print app.left.volts(), app.right.volts()
    print app.left.grams(), app.right.grams()

    port = SERVER_PORT
    # app.left.go_to_top_and_init()
    # app.right.go_to_top_and_init()

    print "192.168.1.18:{}".format(port)

    gevent.joinall([
        gevent.spawn(tight),
        gevent.spawn(update_dash),
        gevent.spawn(programme_countdown),
        socketio.run(app, host="0.0.0.0", port=port, policy_server=False)

    ])

