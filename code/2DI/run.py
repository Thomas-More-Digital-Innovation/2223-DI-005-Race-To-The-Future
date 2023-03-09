#!/usr/bin/env python
from time import sleep
from shooterdriver import ShooterDriver

driver = ShooterDriver()

driver.set_steering_angle(1.0)
sleep(1)
driver.set_steering_angle(-1.0)
sleep(1)
driver.set_steering_angle(0.0)
