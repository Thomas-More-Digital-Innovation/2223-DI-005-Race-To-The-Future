#!/usr/bin/env python
from time import sleep
from shooterdriver import ShooterDriver

driver = ShooterDriver()

# driver.set_steering_angle(1.0)
# sleep(1)
# driver.set_steering_angle(-1.0)
# sleep(1)
# driver.set_steering_angle(0.0)

try:
    driver.set_wheels_speed(-1.0)
    sleep(1)
    driver.set_wheels_speed(0.0)
    sleep(1)
    driver.set_wheels_speed(-0.2)
    sleep(1)
    driver.set_wheels_speed(0)
except KeyboardInterrupt:
    driver.set_wheels_speed(0)
