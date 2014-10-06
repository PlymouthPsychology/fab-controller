import pyfirmata
from time import sleep
from pyfirmata import ArduinoMega, util
import os


def get_board():
    tty = filter(lambda x: "tty.usbmo" in x, os.listdir("/dev/"))

    if not tty:
        raise Exception("No arduino device found")

    if len(tty) > 1:
        ttynum = raw_input("Choose an option:\n" + "\n".join("{}. {}".format(i,j) for i, j in enumerate(tty, 1)) + "\n")
        tty = tty.pop(int(ttynum)-1)
    else:
        tty = tty[0]


    board = ArduinoMega("/dev/"+tty)
    sleep(.5)
    it = util.Iterator(board)
    it.start()

    return board, it
