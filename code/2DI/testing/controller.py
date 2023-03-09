from time import sleep
from evdev import InputDevice, categorize, ecodes

from shooterdriver import ShooterDriver

driver = ShooterDriver()

while True:
   try:
      device = InputDevice('/dev/input/event2')
      break
   except:
      print("try again")
print(device)


for event in device.read_loop():
    try:
        # print(event)
        # if event.type == ecodes.EV_ABS:
        #    print(categorize(event))
        keyevent = categorize(event)
        # right
        if event.code == ecodes.ABS_RZ:
            value = (device.absinfo(ecodes.ABS_RZ).value / 255)
            driver.set_wheels_speed(value)
        #left
        if event.code == ecodes.ABS_Z:
            value = (device.absinfo(ecodes.ABS_Z).value / 255) - 1
            print(value)
            print('---')
            print(-(1+value))
            driver.set_wheels_speed(-(1+value))
        # left axis
        if event.code == ecodes.ABS_X:
            value = (device.absinfo(ecodes.ABS_X).value / 255) -0.25
            driver.set_steering_angle(value)
            print("controller:",device.absinfo(ecodes.ABS_X).value)
            print("value:",value)
    except KeyboardInterrupt:
        print('interrupted!')
        driver.set_steering_angle(0.0)
