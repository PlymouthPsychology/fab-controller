import math
from datetime import datetime
from collections import deque

import gevent
from gevent.pywsgi import WSGIServer
import gevent.monkey
gevent.monkey.patch_all()

from client import log_data, programme_countdown, update_dash, app, socketio
from motors import run_left, run_right, run_motors_to_top_stop
from sensors import poll_sensors, smooth_current_sensor_values, SMOOTHING_WINDOW



# Specify some 'global' variables
app.targets = {'left': 0, 'right': 0, 'timestamp': datetime.now()}
# use a deque for the raw sensor readings for speed, store the last n
app.measurements = {'left': deque(maxlen=SMOOTHING_WINDOW), 'right': deque(maxlen=SMOOTHING_WINDOW)}
app.smoothed = {'left': 0, 'right': 0}
app.blocks = deque()
app.programme_countdown = None


# THIS JOINS ALL THE KEY FUNCTIONS INTO THE CO-OPERATIVE EVENT LOOP
if __name__ == '__main__':
    
    print("Running...")
    gevent.joinall([
        gevent.spawn(update_dash),
        gevent.spawn(run_motors_to_top_stop),
        gevent.spawn(log_data),
        gevent.spawn(poll_sensors),
        gevent.spawn(smooth_current_sensor_values),
        gevent.spawn(run_left),
        gevent.spawn(run_right),
        gevent.spawn(programme_countdown),
        socketio.run(app)
    ])
    
    