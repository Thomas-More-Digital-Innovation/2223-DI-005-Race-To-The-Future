from time import sleep
from shooterdriver import ShooterDriver

driver = ShooterDriver()
# driver.set_steering_angle(-1.0)

def testRit():
   #Go forward
   # driver.set_steering_angle(-1)
   # print("angle -0.2")
   # sleep(2)
   # driver.set_steering_angle(-0.9)
   # print("angle -0.1")
   # sleep(2)
   # driver.set_steering_angle(0.0)
   # sleep(2)
   # driver.set_steering_angle(0.9)
   # print("angle 0.2")
   # sleep(2)
   # driver.set_steering_angle(1)
   # print("angle 0.1")
   # sleep(2)


   # sleep(3)
   # #break (issue with transition backwards)
   # # driver.set_wheels_speed(-0.3)
   # # sleep(1)
   # # driver.set_wheels_speed(0.0)
   # # sleep(1)
   # #backwards plus steer right
   # #driver.set_wheels_speed(-0.3)
   # driver.set_wheels_speed(0.2)
   # driver.set_steering_angle(-0.4)


   #forward plus steer left



def cleanup():
    print('Stopping the car, resetting hardware.')
    driver.set_wheels_speed(0.0)
    driver.set_steering_angle(0.0)


try:
   while True:
      testRit()
except KeyboardInterrupt:
   print('interrupted!')
   cleanup()

