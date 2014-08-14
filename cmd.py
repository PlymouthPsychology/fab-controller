# import RPi.GPIO as GPIO
from settings import MOTOR_PINS, UP, DOWN

# GPIO.setmode(GPIO.BCM)

# set the motor prins to write
# [[GPIO.setup(MOTOR_PINS[h[i]], GPIO.OUT)
#     for i in ['step', 'direction']
#         for h in ['left', 'right']]]

# def digital_read(pin):
#     return GPIO.input(pin)


# def digital_write(pin, val):
#     GPIO.output(pin, val)
#     return (pin, val)


hand = "left"
direction = DOWN

while True:
    inp = raw_input("Enter command ('h' for help): ").strip().upper()

    try:
        if inp in ["H"]:
            print "Enter S for current state, L or R to choose hand, U or D to set direction, or a number to step."

        elif inp in ["S"]:
            print "Currently using", hand, " direction is", {0: 'down', 1: 'up'}[direction]

        elif inp in ["L", "R"]:
            hand = {"L": "left", "R": "right"}[inp]
            print "Setting hand to ", inp

        elif inp in ["U", "D"]:
            direction = {"U": UP, "D": DOWN}[inp]
            print "Setting direction to ", inp

        else:
            steps = int(inp)
            # digital_write(MOTOR_PINS[hand]['direction'], direction)
            print "Stepping ", steps
            # [digital_write(MOTOR_PINS[hand]['step'], True) for i in range(steps)]

    except Exception as e:
        print "Invalid input: ", str(e)
