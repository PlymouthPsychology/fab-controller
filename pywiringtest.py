#wiring is much faster than gpio

from datetime import datetime


import wiringpi
io = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_PINS)
io.pinMode(1,io.OUTPUT)

start = datetime.now()
for i in xrange(100000):
    io.digitalWrite(1,io.HIGH)
    io.digitalWrite(1,io.LOW)
print datetime.now()-start

start = datetime.now()
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
for i in xrange(100000):
    GPIO.output(18,1)
    GPIO.output(18,0)

print datetime.now()-start
