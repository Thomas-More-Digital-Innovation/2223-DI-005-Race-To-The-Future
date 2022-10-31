#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <linux/joystick.h>
#include <stdbool.h>
#include <time.h>

#define SERVO_PWM_PERIOD 20000000
#define SERVO_MAX_DUTY 2100000
#define SERVO_MIN_DUTY 1100000
#define SERVO_DEGREE ((SERVO_MAX_DUTY - SERVO_MIN_DUTY) / 180)
#define WHEELS_SERVO_MAX_DUTY 2100000
#define WHEELS_SERVO_MIN_DUTY 1100000
#define WHEELS_SERVO_DEGREE ((WHEELS_SERVO_MAX_DUTY - WHEELS_SERVO_MIN_DUTY) / 180)

/**
 * Reads a joystick event from the joystick device.
 *
 * Returns 0 on success. Otherwise -1 is returned.
 */
int read_event(int fd, struct js_event *event)
{
	ssize_t bytes;

	bytes = read(fd, event, sizeof(*event));

	if (bytes == sizeof(*event))
		return 0;

	/* Error, could not read full event. */
	return -1;
}

/**
 * Returns the number of axes on the controller or 0 if an error occurs.
 */
size_t get_axis_count(int fd)
{
	__u8 axes;

	if (ioctl(fd, JSIOCGAXES, &axes) == -1)
		return 0;

	return axes;
}

/**
 * Returns the number of buttons on the controller or 0 if an error occurs.
 */
size_t get_button_count(int fd)
{
	__u8 buttons;
	if (ioctl(fd, JSIOCGBUTTONS, &buttons) == -1)
		return 0;

	return buttons;
}

/**
 * Current state of an axis.
 */
struct axis_state
{
	short x, y;
};

/**
 * Keeps track of the current axis state.
 *
 * NOTE: This function assumes that axes are numbered starting from 0, and that
 * the X axis is an even number, and the Y axis is an odd number. However, this
 * is usually a safe assumption.
 *
 * Returns the axis that the event indicated.
 */
size_t get_axis_state(struct js_event *event, struct axis_state axes[3])
{
	size_t axis = event->number / 2;

	if (axis < 3)
	{
		if (event->number % 2 == 0)
			axes[axis].x = event->value;
		else
			axes[axis].y = event->value;
	}

	return axis;
}

int main(int argc, char *argv[])
{
	const char *device;
	int js;
	int steering;
	int wheels;
	char steeringWriteBuffer[8];
	char wheelsWriteBuffer[8];
	bool estop_ok = false;
	struct js_event event;
	struct axis_state axes[3] = {0};
	size_t axis;
	clock_t t;

	if (argc > 1)
		device = argv[1];
	else
		device = "/dev/input/js0";

	js = open(device, O_RDONLY);

	if (js == -1)
		perror("Could not open joystick");

	steering = open("/sys/class/pwm/pwmchip0/pwm1/duty_cycle", O_WRONLY);

	if (steering == -1)
	{
		perror("Cannot open device file...");
	}

	wheels = open("/sys/class/pwm/pwmchip0/pwm0/duty_cycle", O_WRONLY);

	if (wheels == -1)
	{
		perror("Cannot open device file...");
	}

	snprintf(wheelsWriteBuffer, sizeof(wheelsWriteBuffer), "%d\n", SERVO_MIN_DUTY + (SERVO_DEGREE * (int)180));
	write(wheels, wheelsWriteBuffer, sizeof(wheelsWriteBuffer));
	usleep(100 * 1000);
	snprintf(wheelsWriteBuffer, sizeof(wheelsWriteBuffer), "%d\n", SERVO_MIN_DUTY + (SERVO_DEGREE * (int)0));
	write(wheels, wheelsWriteBuffer, sizeof(wheelsWriteBuffer));
	usleep(100 * 1000);
	snprintf(wheelsWriteBuffer, sizeof(wheelsWriteBuffer), "%d\n", SERVO_MIN_DUTY + (SERVO_DEGREE * (int)90));
	write(wheels, wheelsWriteBuffer, sizeof(wheelsWriteBuffer));
	usleep(100 * 1000);

	/* This loop will exit if the controller is unplugged. */
	while (read_event(js, &event) == 0)
	{
		t = clock();
		switch (event.type)
		{
		case JS_EVENT_BUTTON:
			printf("Button %u %s\n", event.number, event.value ? "pressed" : "released");

			if (event.number == 0)
			{
				estop_ok = event.value;

				if (!estop_ok)
				{
					snprintf(steeringWriteBuffer, sizeof(steeringWriteBuffer), "%d\n", SERVO_MIN_DUTY + (SERVO_DEGREE * 90));
					write(steering, steeringWriteBuffer, sizeof(steeringWriteBuffer));
					snprintf(wheelsWriteBuffer, sizeof(wheelsWriteBuffer), "%d\n", WHEELS_SERVO_MIN_DUTY + (WHEELS_SERVO_DEGREE * 90));
					write(wheels, wheelsWriteBuffer, sizeof(wheelsWriteBuffer));
				}
			}

			break;
		case JS_EVENT_AXIS:
			axis = get_axis_state(&event, axes);

			if (axis == 0 && estop_ok)
			{
				float scaledAxis = ((axes[axis].x / 32767.0f) * 90) + 90;
				// printf("%.4f\n", scaledAxis);
				snprintf(steeringWriteBuffer, sizeof(steeringWriteBuffer), "%d\n", SERVO_MIN_DUTY + (SERVO_DEGREE * (int) (180 - scaledAxis)));
				write(steering, steeringWriteBuffer, sizeof(steeringWriteBuffer));
			}

			if (axis == 1 && estop_ok)
			{
				float scaledAxis = ((axes[axis].x / 32767.0f) * 45) + 45;

				if (scaledAxis > 35) {
					scaledAxis = 35;
				}

				// printf("%.4f\n", scaledAxis);
				snprintf(wheelsWriteBuffer, sizeof(wheelsWriteBuffer), "%d\n", WHEELS_SERVO_MIN_DUTY + (WHEELS_SERVO_DEGREE * (int)(90 - scaledAxis)));
				write(wheels, wheelsWriteBuffer, sizeof(wheelsWriteBuffer));
			}

			if (axis == 2 && estop_ok)
			{
				float scaledAxis = ((axes[axis].y / 32767.0f) * 45) + 45;

				if (scaledAxis > 25) {
					scaledAxis = 25;
				}

				// printf("%.4f\n", scaledAxis);
				snprintf(wheelsWriteBuffer, sizeof(wheelsWriteBuffer), "%d\n", WHEELS_SERVO_MIN_DUTY + (WHEELS_SERVO_DEGREE * (int)(scaledAxis + 90)));
				write(wheels, wheelsWriteBuffer, sizeof(wheelsWriteBuffer));
			}

			if (axis < 3)
				printf("Axis %zu at (%6d, %6d)\n", axis, axes[axis].x, axes[axis].y);
			break;
		default:
			/* Ignore init events. */
			break;
		}

		t = clock() - t;
		double time_taken = (((double)t) / CLOCKS_PER_SEC) * 1000 * 1000; // in seconds
		printf("handler took %f microseconds to execute \n", time_taken);

		fflush(stdout);
	}

	close(js);
	return 0;
}
