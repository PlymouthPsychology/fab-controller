import gevent
import gevent.monkey
gevent.monkey.patch_all()

from settings import *
from pyfirmata import util
from getarduino import get_board
board, boarditer = get_board()



left_sensor = board.get_pin('a:{}:i'.format(SENSOR_PIN.left))
right_sensor = board.get_pin('a:{}:i'.format(SENSOR_PIN.right))

gevent.sleep(.2)

print "sensor readings:", left_sensor.read(), right_sensor.read()


def pulse(pin, delay=.0001, n=1):
    for i in range(n):
        pin.write(0)
        gevent.sleep(delay)
        pin.write(1)


led = board.get_pin('d:13:o')

left_step = board.get_pin('d:{}:o'.format(STEP_PIN.left))
left_direction = board.get_pin('d:{}:o'.format(DIRECTION_PIN.left))

right_step = board.get_pin('d:{}:o'.format(STEP_PIN.right))
right_direction = board.get_pin('d:{}:o'.format(DIRECTION_PIN.right))


left_limit = board.get_pin('d:{}:i'.format(HIGH_LIMIT_PIN.left))
right_limit = board.get_pin('d:{}:i'.format(HIGH_LIMIT_PIN.right))

for i in range(5):
    print "switches: ", left_limit.read(), right_limit.read()
    gevent.sleep(.5)



board.exit()





# def updown(step, direction):
#     for i in range(20):
#         direction.write(1)
#         pulse(step, n=100)
#         direction.write(0)
#         pulse(step, n=100)
#         gevent.sleep()


# leftp = lambda: updown(left_step, left_direction)
# rightp = lambda: updown(right_step, right_direction)



# gevent.joinall([
#     gevent.spawn(rightp),
#     gevent.spawn(leftp),
# ])


