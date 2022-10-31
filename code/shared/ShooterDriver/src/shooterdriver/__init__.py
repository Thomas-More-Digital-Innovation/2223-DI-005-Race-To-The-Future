from time import sleep


class ShooterDriver:
    """
    ShooterDriver is used to control the RTTF car.
    """
    SERVO_PWM_PERIOD = 20000000
    SERVO_MAX_DUTY = 2100000
    SERVO_MIN_DUTY = 1100000
    SERVO_INCREMENT = (SERVO_MAX_DUTY - SERVO_MIN_DUTY) / 200

    WHEELS_PWM_PERIOD = 20000000
    WHEELS_MAX_DUTY = 2100000
    WHEELS_MIN_DUTY = 1100000
    WHEELS_INCREMENT = (SERVO_MAX_DUTY - SERVO_MIN_DUTY) / 200

    PATH_STEERING_DUTY = "/sys/class/pwm/pwmchip0/pwm1/duty_cycle"
    PATH_WHEELS_DUTY = "/sys/class/pwm/pwmchip0/pwm0/duty_cycle"

    def __init__(self):
        self.fh_steering = open(ShooterDriver.PATH_STEERING_DUTY, "w")
        self.fh_wheels = open(ShooterDriver.PATH_WHEELS_DUTY, "w")

        self._init_wheels()

    def _write_steering(self, angle: float) -> None:
        """
        Write to the steering file handle.
        :param angle: float of the PWM angle
        :return:
        """
        self.fh_steering.write(f"{int(angle)}\n")

        # Flush the buffer after every write because Python caches writes by default in a buffer.
        self.fh_steering.flush()

    def _write_wheels(self, speed: float) -> None:
        """
        Write to the wheels file handle.
        :param speed: float of the PWM speed
        :return:
        """
        self.fh_wheels.write(f"{int(speed)}\n")

        # Flush the buffer after every write because Python caches writes by default in a buffer.
        self.fh_wheels.flush()

    def _init_wheels(self) -> None:
        """
        Initialise the motor controller. This is required to set the correct speed values.
        Steps:
            1. Full speed backward
            2. Full speed forward
            3. Idle
        :return:
        """
        self.set_wheels_speed(-1.0)
        sleep(0.01)
        self.set_wheels_speed(1.0)
        sleep(0.01)
        self.set_wheels_speed(0.0)
        sleep(0.01)

    def set_steering_angle(self, angle: float) -> None:
        """
        Set the angle of the wheels using a float.
        :param angle: float where -1.0 is left, 1.0 is right and 0.0 is straight.
        :return:
        """
        if angle > 1.0 or angle < -1.0:
            raise ValueError(f"Steering angle out of range. Expected -1.0 < i < 1.0. Got {angle}")

        computed_range = (-angle + 1) * 100
        computed_angle = ShooterDriver.SERVO_MIN_DUTY + (ShooterDriver.SERVO_INCREMENT * computed_range)

        self._write_steering(computed_angle)

    def set_wheels_speed(self, speed: float) -> None:
        """
        Set the speed of the wheels using a float.
        :param speed: float where -1.0 is backwards, 1.0 is forwards and 0.0 is idle.
        :return:
        """
        if speed > 1.0 or speed < -1.0:
            raise ValueError(f"Wheel speed out of range. Expected -1.0 < i < 1.0. Got {speed}")

        computed_range = (speed + 1) * 100
        computed_speed = ShooterDriver.WHEELS_MIN_DUTY + (ShooterDriver.WHEELS_INCREMENT * computed_range)

        self._write_wheels(computed_speed)
