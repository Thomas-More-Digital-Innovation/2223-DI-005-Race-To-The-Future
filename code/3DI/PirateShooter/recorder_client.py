#!/usr/bin/env python3
import datetime
import functools
import grpc
import logging
import numpy
from recorder.recorder import Recorder
from recorder.proto import recorder_pb2, recorder_pb2_grpc


SERVER_ADDRESS = 'localhost:50051'


def callback(latest_timestamp, latest_steering_input, latest_wheel_input, latest_image: numpy.ndarray, stub: recorder_pb2_grpc.RecorderServiceStub):
    if latest_image is None:
        return

    datetime_timestamp = datetime.datetime.fromtimestamp(latest_timestamp)

    datapoint = recorder_pb2.SendDataPointRequest(
        timestamp=None, steering_angle=latest_steering_input, wheel_speed=latest_wheel_input, image=latest_image.tobytes())

    # put this outside of the constructor, else the timestamp will not be set in the message
    datapoint.timestamp.FromDatetime(dt=datetime_timestamp)

    stub.SendDataPoint(datapoint)


def main():
    logging.basicConfig(format='%(levelname)s:%(message)s',
                        level=logging.DEBUG)

    channel = grpc.insecure_channel(SERVER_ADDRESS)
    stub = recorder_pb2_grpc.RecorderServiceStub(channel)

    recorder = Recorder('/dev/input/event20', 0,
                        functools.partial(callback, stub=stub))

    try:
        recorder.start()
        recorder.run_indefinitely()
    except KeyboardInterrupt:
        recorder.stop()


if __name__ == "__main__":
    main()
