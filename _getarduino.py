import pyfirmata
from time import sleep
from pyfirmata import ArduinoMega, util
import os


def get_board():
    tty = [x for x in os.listdir("/dev/") if "tty.usbmo" in x]

    if not tty:
        raise Exception("No arduino device found")

    if len(tty) > 1:
        ttynum = input("Choose an option:\n" + "\n".join("{}. {}".format(i,j) for i, j in enumerate(tty, 1)) + "\n")
        tty = tty.pop(int(ttynum)-1)
    else:
        tty = tty[0]


    board = ArduinoMega("/dev/"+tty)
    sleep(.5)
    
    it = util.Iterator(board)
    it.start()

    return board, it
