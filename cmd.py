import time
from settings import *
from py_io import *
# import gevent.monkey
# gevent.monkey.patch_all()

if __name__ == '__main__':
    hand = "left"

    print("Enter command ('h' for help): ")
    while 1:
        inp = raw_input("> ").strip().upper()
        try:
            if inp in ["H"]:
                print("Enter S for current state, L or R to choose hand, U or D to set direction, or a number to step.")

            elif inp in ["S"] or not inp:
                print("Currently controlling {}, direction is {}".format(
                    hand, MOVEMENT_LABELS[direction]))
                print("Readings: ", weights())

            elif inp in ["U", "D"]:
                new_direction = {"U": UP, "D": DOWN}[inp]
                print("Setting direction to {}".format(new_direction))
                DIRECTIONS = Pair(*[digital_write(getattr(DIRECTION, i), new_direction)
                    for i in HANDS])

            elif inp in ["L", "R"]:
                hand = {'L': 'left', 'R': 'right'}[inp]
                print("Setting hand to {}".format(hand))

            else:
                nsteps = int(inp)
                print("Stepping {} {} steps {}".format(hand, nsteps, getattr(DIRECTIONS, hand)))
                [pulse_motor(getattr(STEP, hand)) for i in xrange(nsteps)]

        except Exception as e:
            print("Invalid input: {}".format(str(e)))
