import logging
import cv2
from shooterdriver import ShooterDriver
from test import HandCodedLaneFollower
from picamera2 import Picamera2
3280 2464
class DeepPiCar(object):
    driver = ShooterDriver()

    __INITIAL_SPEED = 0.0


    def __init__(self):
        """ Init camera and wheels"""
        logging.info('Creating a DeepPiCar...')

        logging.debug('Set up camera')
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1280, 720)}))
        picam2.start()
        self.camera  = cv2.blur(picam2.capture_array(),(7,7),cv2.BORDER_DEFAULT)
        self.lane_follower = HandCodedLaneFollower(self)

        logging.info('Created a DeepPiCar')


    def __enter__(self):
        """ Entering a with statement """
        return self

    def __exit__(self, _type, value, traceback):
        """ Exit a with statement"""
        if traceback is not None:
            # Exception occurred:
            logging.error('Exiting with statement with exception %s' % traceback)

        self.cleanup()

    def cleanup(self):
        """ Reset the hardware"""
        logging.info('Stopping the car, resetting hardware.')
        self.driver.set_wheels_speed(0.0)
        self.driver.set_steering_angle(0.0)

    def drive(self, speed=__INITIAL_SPEED):
        """ Main entry point of the car, and put it in drive mode
        Keyword arguments:
        speed -- speed of back wheel, range is 0 (stop) - 100 (fastest)
        """

        logging.info('Starting to drive at speed %s...' % speed)
        self.driver.set_wheels_speed(speed)

        while self.camera.isOpened():
            _, image_lane = self.camera.read()
            image_lane = self.follow_lane(image_lane)
            cv2.imwrite('Lane_Lines.png', image_lane)




    def follow_lane(self, image):
        image = self.lane_follower.follow_lane(image)
        return image


############################
# Utility Functions
############################


def main():
    with DeepPiCar() as car:
        car.drive(0.1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-5s:%(asctime)s: %(message)s')
    main()

