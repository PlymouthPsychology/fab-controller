import json
from datetime import datetime
from collections import namedtuple
from flask.ext.socketio import emit
import gevent


def stopall():
    [i.kill() for i in app.blocks]
    app.blocks.clear()
    set_block_targets(0, 0)
    app.programme_countdown = None
    socketio.emit('log', {'message': "Stopping"})



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

