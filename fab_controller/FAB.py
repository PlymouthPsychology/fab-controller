#!/usr/bin/env python
import functools
import json
import webbrowser
from collections import deque
from datetime import datetime
import os
import re
import signal
import sys
import pyfirmata
from time import sleep
from pyfirmata import ArduinoMega, util

from flask import Flask, Response, redirect
from flask_socketio import SocketIO, send, emit
import gevent
from settings import *



app = Flask(__name__, )
app.config['debug'] = False
socketio = SocketIO(app)
app.blocks = deque()
app.programme_countdown = None
app.logfilename = "log.txt"  # a default
app.logfilepath = LOGFILE_DIR

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response



def get_arduino_name():
    """Tries to find an Arduino acting as a usb modem. If multiple
    candidates found asks user to select one."""

    tty = [x for x in os.listdir("/dev/") if "tty.usbmo" in x]

    if not tty:
        raise Exception("No arduino device found")

    if len(tty) > 1:
        ttynum = input("Choose an option:\n" + "\n".join("{}. {}".format(i,j) for i, j in enumerate(tty, 1)) + "\n")
        tty = tty.pop(int(ttynum)-1)
    else:
        tty = tty[0]

    return "/dev/" + tty


def get_board(tty):
    """Acquires the named Arduino and starts an interator."""
    
    board = ArduinoMega(tty)
    sleep(.5)
    
    it = util.Iterator(board)
    it.start()

    return board, it


# THIS IS IMPORTANT!!
# If board.exit() not fired the board will need to be unplgged and 
# plugged in again to work correctly.
def cleanup_board_signal_handler(signal, frame):
    print('You pressed Ctrl+C! Cleaning up...')
    board.exit()
    sys.exit(0)




def setup_pins(board):

    # Build a dictionary of the pins on the actual board from our settings file.
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

    # Turn on reporting on the sensor pins. 
    live_pins['left']['sensor_pin'].enable_reporting()
    live_pins['right']['sensor_pin'].enable_reporting()

    return live_pins



def check_pins(live_pins):
    # PIN SETUP
    # This could be moved into the Crusher init function.
    print("Checking switches and sensors are live...")
    print live_pins
    gevent.joinall([
                gevent.spawn(check_pin, live_pins['left']['high_limit_pin'], live_pins, hand="left"),
                gevent.spawn(check_pin, live_pins['right']['high_limit_pin'], live_pins, hand="right"),
                gevent.spawn(check_pin, live_pins['left']['sensor_pin'], live_pins),
                gevent.spawn(check_pin, live_pins['right']['sensor_pin'], live_pins),
            ], 
        timeout=15, 
        raise_error=True
    )

    return True


# this could be moved into the Crusher init function.
print("Checking switches and sensors are live...")

def check_pin(pin, live_pins, hand=None):
    # range for loop specifies max tries or steps down before giving up 
    for i in xrange(1000):
        if pin.read() is not None:
            return True
        if hand:
            # this logic is because depressed switches read None forever
            live_pins[hand]['direction_pin'].write(DOWN)
            live_pins[hand]['step_pin'].write(1)
            gevent.sleep(STEP_DELAY)
            live_pins[hand]['step_pin'].write(0)
            gevent.sleep(STEP_DELAY)

        gevent.sleep(STEP_DELAY)

    raise Exception("{} cannot be recognised".format(pin))



def scale_range(x, OldMin, OldMax, NewMin, NewMax):
    """Scale a value in range (a,b) to corresponding value in range (c,d)"""    
    try:
        return (((x - OldMin) * (NewMax - NewMin)) / (OldMax - OldMin)) + NewMin
    except ZeroDivisionError as e:
        _log_session_data({'message': "Error ({}). Are you sure 2kg is applied?".format(e)})
        raise 




class Crusher(object):
    """Manages a finger crusher, including sensor, motor and limit switches."""

    direction = None
    steps_from_top = 3000  # note this may not be correct on switch on, but we will initialise by driving to top
    target = None

    def __init__(self, zero, twokg, live_pins, name="leftorright"):

        self.live_pins = live_pins

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
        # not tracking bottom switches yet

    def set_direction(self, direction):
        if self.direction != direction:
            self.live_pins[self.name]['direction_pin'].write(direction)
            self.direction = direction

    def _switch_state_generator(self, position):
            """Introduce min delay in readings and hysteresis for change in state.
            A generator is used to preserve the window of n measurements across calls.
            """

            if position == "top":
                pin = self.live_pins[self.name]['high_limit_pin']
            else:
                pin = self.live_pins[self.name]['low_limit_pin']

            windowlen = SWITCH_CHECKING_WINDOW_LENGTH
            window = deque(maxlen=windowlen)
            window.extend([True] * windowlen)
            state = False

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
            if self.pulse() < 1:
                break
            gevent.sleep(0.0001)


    def go_to_top_and_init(self):

        _log_session_data({'message': "Moving down slightly"})
        self.set_direction(DOWN)
        gevent.sleep(.1)
        self.pulse(n=100)

        
        _log_session_data({ 'message': "Moving {} to top to initialise.".format(self.name)})
        self.go_to_top()

        self.steps_from_top = 0
        _log_session_data({ 'message':  "{} is at top limit switch.".format(self.name)})

        self.set_direction(DOWN)
        gevent.sleep(.1)
        for i in range(REST_N_FROM_TOP):
            self.pulse()
            gevent.sleep(.0001)

        _log_session_data({ 'message':  "{} is ready.".format(self.name)})

    def pulse(self, n=1):
        """Pulse the stepper motor if safe to do so. Return error code or
        number of steps.
        """

        AT_TOP = -1
        AT_BOTTOM = -2

        self.update_switch_states()

        if self.direction is DOWN and self.steps_from_top >= (MAX_STEPS - n) and not self.at_bottom:
            print(self.name, "too low to step. Now at ", self.steps_from_top, "Need to step ", n)
            return AT_BOTTOM

        if self.direction is UP:
            # don't go within 100 steps of the top for safety/smoothness
            if self.steps_from_top <= 100 or self.at_top:
                print(self.name, "too high to step. Now at ", self.steps_from_top, ". At-top=", self.at_top, ". Need to step ", n)
                
                # reset the counter if we have somehow got to the top switch, e.g. by skipping or miscounting steps
                if self.at_top:  
                    self.steps_from_top = 0
                
                return AT_TOP

        # do the stepping
        p = self.live_pins[self.name]['step_pin']
        for i in range(n):
            p.write(1)
            gevent.sleep(STEP_DELAY)
            p.write(0)
            gevent.sleep(STEP_DELAY)

        # Update the internal step counter
        if self.direction == DOWN:
            self.steps_from_top += n
        else:
            self.steps_from_top += -n
        
        return n

    def analog_reading(self):
        """Not actually volts - just the input from the analog input"""
        return self.live_pins[self.name]['sensor_pin'].read()

    def zero_sensor(self):
        self.zero = self.analog_reading()
        msg = "Setting zero point for {} to analog reading: {}".format(self.name, self.zero)
        _log_session_data({'message': msg})

    def grams(self):
        """Scale using parameters in settings. Note parameters for each hand/sensor may differ."""
        g = scale_range(self.analog_reading(), self.zero, self.twokg, 0, 2000)
        return max([g, 0])

    def _update_direction(self, delta):
        "Decide to go up or down now based on the difference between target and sensor readings."
        d = delta > 0 and DOWN or UP  # i.e. if target is bigger than grams we go down
        self.set_direction(d)

    def track(self):
        """Pulse and change direction to track target weight."""

        if not self.tracking:
            return

        nsamples = SENSOR_MEASUREMENTS_WINDOW_LENGTH
        margin = max([ALLOWABLE_DISCREPANCY, self.target * .05])

        # Delta is positive when target > grams
        delta = self.target - (sum(self.grams() for i in range(nsamples)) / nsamples)
        adelta = abs(delta) + 1

        # Only do the work if outside our margin of error.
        if adelta > margin:
            self._update_direction(delta)
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
    try:
        app.left.target = l
        app.right.target = r
        _log_session_data({'targets': Pair(l, r)})

    except AttributeError as e:
        _log_session_data({'message': "Can't set target:{}".format(e)})



@socketio.on('new_program')
def run_program_from_json(jsondata):
    prog = validate_json_program(jsondata)
    if prog:
        _log_session_data({'programme': prog, "message": "Running program."},)
        schedule_program_for_execution(prog)

@socketio.on('set_logfile_name')
def set_logfile_name(data):
    app.logfilename = data.get("logfilename", "log.txt")
    _log_session_data({'message': "Updated logfilename to {}".format(app.logfilename)})


def _log_session_data(data):
    """Write a dictionary as a string to a line in the logfile."""

    if not isinstance(data, dict):
        data = {'message': data}

    if data.get('message', None):
        socketio.emit('actionlog', data.get('message'))

    data.update({'timestamp': datetime.now()})
    with open(os.path.join(LOGFILE_DIR, app.logfilename), "a") as f:
        f.write(str(data) + "\n")
    

@socketio.on('log_session_data')
def log_session_data(data):
    """Socket handler to write to log from client."""

    return _log_session_data(data)


@socketio.on('quit')
def quit(data):
    """."""
    import sys
    sys.exit()



@socketio.on('restonfingers')
def restonfingers(x):
    """Apply just 20g to give a consistent starting point for pre-programmed sessions."""
    try:
        app.left.target = 50
        app.right.target = 50
        _log_session_data({'message': "Rest on fingers"})

    except AttributeError as e:
        _log_session_data({'message': "Error resting on fingers: " + str(e)})

@socketio.on('toggle_tracking')
def toggle_tracking(x):
    app.left.tracking = not app.left.tracking
    app.right.tracking = not app.right.tracking
    print("Toggled tracking (left, right) to:", app.left.tracking, app.right.tracking)

@socketio.on('zero_sensor')
def zero_sensors(x):
    """Reset our expected value from the sensor for when zero pressure applied. 
    Potentially useful for calibration."""
    app.left.zero_sensor()
    app.right.zero_sensor()
    print("Reset Zero point for both sensors")

@socketio.on('mark_twokg')
def mark_twokg(data):
    """Reset our expected value from the sensor for when 2kg applied."""
    crusher = getattr(app, data['hand'])
    crusher.twokg = crusher.analog_reading()
    print("Set 2kg value for {} to {}".format(crusher.name, crusher.twokg))

@socketio.on('manual_pulse')
def manual_pulse(data):
    print("Executing manual pulses", str(data))
    crusher = getattr(app, data['hand'])
    crusher.set_direction(MOVEMENT[data['direction'].lower()])
    crusher.pulse(n=int(data['n']))

@socketio.on('stopall')
def stop_everything(data):
    stopall()


def stopall():
    _log_session_data({'message': "Stop button pressed."})
    
    # clear any program data and reset targets
    [i.kill() for i in app.blocks]
    app.blocks.clear()
    app.programme_countdown = None
    set_block_targets(Pair(0, 0))
    


@socketio.on('return_to_stops')
def return_to_stops(data):
    _log_session_data({'message': "Returning pistons to top stops."})
    stopall()

    try:
        # we join these functions so they happen simultaneously
        gevent.joinall([
            gevent.spawn(app.left.go_to_top),
            gevent.spawn(app.right.go_to_top),
        ])
    except AttributeError as e:
        _log_session_data({'message': str(e)})

@socketio.on('lift_slightly')
def lift_slightly(x):
    _log_session_data({'message': "Lifting both pistons slightly."})

    app.left.set_direction(UP)
    app.right.set_direction(UP)

    # join to simultenaeity
    gevent.joinall([
        gevent.spawn(app.left.pulse, 300),
        gevent.spawn(app.right.pulse, 300)
    ])
    


@socketio.on('disconnect',)
def test_disconnect():
    print('Client disconnected')


# Helper functions

def build_log_entry(app):
    return {
        'target_L': app.left.target,
        'target_R': app.right.target,
        'sensor_L': app.left.grams(),
        'volts_L': app.left.analog_reading(),
        'sensor_R': app.right.grams(),
        'volts_R': app.right.analog_reading(),
        'time': datetime.now().isoformat(),
        'remaining': app.programme_countdown and int(app.programme_countdown) or None,
        'steps_from_top_L': app.left.steps_from_top,
        'steps_from_top_R': app.right.steps_from_top,
        'logfile': app.logfilename,
        'logfilepath': app.logfilepath,
        'version': FAB_VERSION,
    }


def get_list_item_or_none(l, i):
    try:
        return l[i]
    except IndexError:
        return None

def int_or_prompt(s):
    try: 
        return int(s)
    except:
        assert s.strip() in ["left", "right"]
        return s.strip()

def validate_json_program(jsondata):

    try:
        lines = [x for x in jsondata['data'].splitlines() if x.strip()]  # strip whitespace
        lines = filter(lambda x: not x.strip().startswith("#"), lines) # get rid of comments
        lines = [x for x in lines if x[0] is not "#"]  # remove comments
        lines = [re.split('\W+|[,]', i) for i in lines]  # split duration, left, right

        prog_ints = [list(map(int_or_prompt, i)) for i in lines]  # we need integers
        socketio.emit('actionlog', "Program validated" )
        return [Block(x[0], Pair(x[1], x[2]), get_list_item_or_none(x,3)) for x in prog_ints]  # return blocks

    except Exception as e:
        msg = "Program error: {}".format(e)
        socketio.emit('actionlog', msg )
        return False



def schedule_program_for_execution(prog):

    stopall()  # clear everything already in the queue
    prog = deque(prog)  # because we want to popleft on this

    _log_session_data({"Program": prog, "message": "Scheduling" })

    def add_blocks_keeping_running_time(programme, blocks, cumtime):
        """Recursive function to spawn a list of future blocks from a user program.

        Return tuple of the blocks and the total running time of the programme.
        """
        if not programme:
            # we've come to the end of the programme, so set last block with weight=0 and return.
            print("finished building blocks from prog")
            blocks.append(gevent.spawn_later(cumtime, set_block_targets, Pair(0, 0)))
            blocks.append(gevent.spawn_later(cumtime, _log_session_data, *({'message': "Program complete"})))
            return (blocks, cumtime)
        
        else:
            # take the next block and adjust the weight
            block = programme.popleft()
            blocks.append(gevent.spawn_later(cumtime, set_block_targets, *(block.grams, )))
            
            # also send a prompt if needed
            if block.prompt:
                blocks.append(gevent.spawn_later(cumtime, send_prompt, *(block.prompt, )))
            
            return add_blocks_keeping_running_time(programme, blocks, cumtime + block.duration)

    app.blocks, app.programme_countdown = add_blocks_keeping_running_time(prog, deque(), 0)
    print(app.blocks, app.programme_countdown)


def send_prompt(hand):
    socketio.emit('sayprompt', { "hand": hand} )
    _log_session_data({"prompt": hand, "message": "Sending prompt: {}".format(hand)})

def set_block_targets(grams):
    """Set target forces."""
    try:
        app.left.target, app.right.target = grams  # note tuple unpacking here
    except AttributeError as e:
        print e

    _log_session_data({"target": grams, "message": "Setting target: {}".format(grams)})



# THESE LOOPING FUNCTIONS ARE JOINED TOGETHER BY GEVENT FOR CONCURRENCY

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
    """Updates the dashboard."""
    while 1:
        jsondata = json.dumps(build_log_entry(app))
        socketio.emit('update_dash', {'data': jsondata})
        gevent.sleep(DASHBOARD_UPDATE_INTERVAL)


def tight():
    """Our tight loop which runs to update the pressures."""
    while 1:
        app.left.track()
        app.right.track()
        gevent.sleep(TIGHT_LOOP_INTERVAL)


def open_interface(port):
    print("Opening user interface in browser window")
    try:
        if sys.platform.startswith('win'):
            c = webbrowser.get('windows-default')
        elif sys.platform.startswith('darwin'):
            c = webbrowser.get('safari')
        else:
            c = webbrowser.get('firefox')
        
        c.open("127.0.0.1:{}".format(port), new=0, autoraise=True)

    except:
        print("Couldn't open a web browser. Please open http://127.0.0.1:{} in a web browser".format(SERVER_PORT))
    
    
def log_sensors():
    while 1:
        if app.left.target > 0 or app.right.target > 0:
            _log_session_data({
                'measurement': Pair(app.left.grams(), app.right.grams()),
                'targets': Pair(app.left.target, app.right.target),
            })

        gevent.sleep(LOG_INTERVAL)
