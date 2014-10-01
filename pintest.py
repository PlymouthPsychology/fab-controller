from time import sleep

import wiringpi2 as wiringpi
from ABElectronics_ADCPi import ADCPi

from settings import *


print "Registering sensors"
ADC = ADCPi(SENSOR_CHANNEL_CODE.left, SENSOR_CHANNEL_CODE.right, SENSOR_SAMPLE_RATE)
print "Sensor values: ", ADC.readVoltage(1), ADC.readVoltage(2)


print "Registering GPIO board and ",
io = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_PINS)

print "setting pin modes."
io.pinMode(STEP_PIN.left, io.OUTPUT)
io.pinMode(STEP_PIN.right, io.OUTPUT)
io.pinMode(DIRECTION_PIN.left, io.OUTPUT)
io.pinMode(DIRECTION_PIN.right, io.OUTPUT)

io.pinMode(HIGH_LIMIT_PIN.left, io.INPUT)
io.pinMode(HIGH_LIMIT_PIN.right, io.INPUT)
io.pullUpDnControl(HIGH_LIMIT_PIN.left, WIRING_PULL_UP)
io.pullUpDnControl(HIGH_LIMIT_PIN.right, WIRING_PULL_UP)



print "\nMoving left then right crusher down 100, up 100"

p = lambda x: (io.digitalWrite(x,1), sleep(.001), io.digitalWrite(x,0))

print "down"
io.digitalWrite(DIRECTION_PIN.left, DOWN)
io.digitalWrite(DIRECTION_PIN.right, DOWN)
_=[p(STEP_PIN.left) for i in range(100)]
_=[p(STEP_PIN.right) for i in range(100)]

print "up"
io.digitalWrite(DIRECTION_PIN.left, UP)
io.digitalWrite(DIRECTION_PIN.right, UP)
_=[p(STEP_PIN.left) for i in range(100)]
_=[p(STEP_PIN.right) for i in range(100)]


print "\n Checking limit switches"

print "Moving left down, ",
io.digitalWrite(DIRECTION_PIN.left, DOWN)
_=[p(STEP_PIN.left) for i in range(300)]

print "Moving left to top "
io.digitalWrite(DIRECTION_PIN.left, UP)
while not io.digitalRead(HIGH_LIMIT_PIN.left):
    p(STEP_PIN.left)
    sleep(.0005)

print "Left at top limit. Switch reading: ", io.digitalRead(HIGH_LIMIT_PIN.left)


print "\nMoving right down, ",
io.digitalWrite(DIRECTION_PIN.right, DOWN)
_=[p(STEP_PIN.right) for i in range(300)]

print "moving right to top "
io.digitalWrite(DIRECTION_PIN.right, UP)
while not io.digitalRead(HIGH_LIMIT_PIN.right):
    p(STEP_PIN.right)
    sleep(.0005)

print "Right at top limit. Switch reading: ", io.digitalRead(HIGH_LIMIT_PIN.right),

