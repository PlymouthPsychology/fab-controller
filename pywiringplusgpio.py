import wiringpi
io = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_PINS)
io.pinMode(5, io.OUTPUT)


import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN)


def handle(x):
    print "here"

GPIO.add_event_detect(17,
    GPIO.BOTH,
    callback=handle,
    bouncetime=500)


while 1:
    io.digitalWrite(5,io.HIGH)
    io.digitalWrite(5,io.LOW)
