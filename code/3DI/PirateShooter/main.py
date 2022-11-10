#!/usr/bin/env python3
import asyncio
import datetime
import pickle
import threading
import time

import cv2
from evdev import ecodes, ff
import evdev

from recorder.model.datapoint import DataPoint

datapoints = []

# devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
#
# for device in devices:
#     print(device.path, device.name, device.phys)

device = evdev.InputDevice('/dev/input/event20')
print(device)
print(device.capabilities(verbose=True, absinfo=True))

background_tasks = set()
run = True
image = None
image_lock = threading.Lock()


def controller_input_loop():
    global image
    global run

    for event in device.read_loop():
        if event.type == 0:
            continue

        if event.code == ecodes.BTN_SOUTH:
            print('Exiting loop...')
            break

        if event.code in [ecodes.ABS_RZ, ecodes.ABS_Z, ecodes.ABS_X]:
            timestamp = event.timestamp()
            steering_angle = 0.0
            wheels_speed = 0.0

            if event.code == ecodes.ABS_RZ:
                wheels_speed = event.value / 255

            if event.code == ecodes.ABS_Z:
                wheels_speed = (1 - (event.value / 255)) - 1

            if event.code == ecodes.ABS_X:
                steering_angle = (event.value / 255) * 2 - 1

            with image_lock:
                datapoint = DataPoint(timestamp, steering_angle, wheels_speed, image)
                datapoints.append(datapoint)
                print(datapoint.timestamp, datapoint.steering_angle, datapoint.wheel_speed)

    run = False

    with open("datapoints.pickle", 'wb') as pickle_file:
        pickler = pickle.Pickler(pickle_file, protocol=pickle.HIGHEST_PROTOCOL)

        pickler.dump(datapoints)


def get_camera_images():
    global image
    global run

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        exit(1)

    while run:
        ret, frame = cap.read()

        if not ret:
            print("Can't receive frame, stream ended? Exiting...")
            exit(1)

        with image_lock:
            image = frame


def main():
    image_thread = threading.Thread(target=get_camera_images)
    image_thread.start()

    controller_thread = threading.Thread(target=controller_input_loop)
    controller_thread.start()

    controller_thread.join()
    image_thread.join()


main()
