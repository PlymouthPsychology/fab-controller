from painmachine import app, socketio, Crusher, GPIO, io
import gevent
import gevent.monkey
gevent.monkey.patch_all()
from settings import *
from flask import Flask, Response, redirect


@app.route('/')
def hello():
    return redirect("/index.html", code=302)


@app.route('/<path:path>')
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)


@socketio.on('set_manual')
def set_manual(forces):
    l, r = (forces['left'] * 20, forces['right'] * 20)
    app.left.target = l
    app.right.target = r
    print (l, r)


@socketio.on('stopall')
def stopall():
    app.left.target = 0
    app.left.go_to_top_and_init()
    print "Stopping everything"


if __name__ == "__main__":

    app.left = Crusher(
        HIGH_LIMIT_PIN.left,
        STEP_PIN.left,
        DIRECTION_PIN.left,
        1,
        ALPHA.left,
        BETA.left,
        "left"
    )
    app.right = Crusher(
        HIGH_LIMIT_PIN.right,
        STEP_PIN.right,
        DIRECTION_PIN.right,
        2,
        ALPHA.right,
        BETA.right,
        "right"
    )

    print app.left.grams(), app.right.grams()

    app.left.go_to_top_and_init()
    app.right.go_to_top_and_init()
    gevent.joinall([
        # gevent.spawn(update_dash),
        gevent.spawn(app.left.track),

        # gevent.spawn(app.right.track),
        socketio.run(app, host="0.0.0.0", port=9096, policy_server=False)
    ])
