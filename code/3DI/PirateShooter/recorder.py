#!/usr/bin/env python3
import datetime
import logging
import os
import pickle
import time
from recorder.recorder import Recorder
from recorder.model.datapoint import DataPoint

OUTPUT_FILE = "datapoints.pickle"

datapoints = []


def callback(latest_timestamp, latest_steering_input, latest_wheel_input, latest_image):
    print(latest_timestamp, latest_steering_input, latest_wheel_input)

    datapoint = DataPoint(
        latest_timestamp, latest_steering_input, latest_wheel_input, latest_image)
    datapoints.append(datapoint)


def main():
    start_time = datetime.datetime.now()

    logging.basicConfig(format='%(levelname)s:%(message)s',
                        level=logging.DEBUG)

    recorder = Recorder('/dev/input/event20', 0, callback)

    try:
        recorder.start()
        recorder.run_indefinitely()
    except KeyboardInterrupt:
        recorder.stop()

        time.sleep(0.5)

        with open(OUTPUT_FILE, 'wb') as pickle_file:
            pickler = pickle.Pickler(
                pickle_file, protocol=pickle.HIGHEST_PROTOCOL)
            pickler.dump(datapoints)

        total_time = datetime.datetime.now() - start_time
        file_size = os.path.getsize(OUTPUT_FILE)

        bytes_per_second = (file_size / total_time.total_seconds()) / 1000

        logging.info("recording averaged at %.2f kilobytes per second" %
                     bytes_per_second)


if __name__ == "__main__":
    main()
