
import logging
import math
from time import sleep
import cv2
import numpy as np

from picamera2 import Picamera2
from shooterdriver import ShooterDriver

driver = ShooterDriver()

#steer car based on detected lines
def follow_lane(frame):
    # Main entry point of the lane follower
    cv2.imwrite("orig.png", frame)
    print('image taken frame process')
    lane_lines, frame = detect_lane(frame)
    final_frame = steer(frame, lane_lines)

    return final_frame

#set steering angle
def steer(frame, lane_lines):
    logging.debug('steering...')
    new_steering_angle = 0.0
    if len(lane_lines) == 0:
        new_steering_angle = 0.0
        driver.set_wheels_speed(0.18)
        logging.error('No lane lines detected, nothing to do.')
        return frame

    new_steering_angle = compute_steering_angle(frame, lane_lines)

    old_steering_angle = compute_steering_angle_oldVersion(frame, lane_lines)
    # old_curr_steering_angle = stabilize_steering_angle(curr_steering_angle, old_steering_angle, len(lane_lines))    

    # curr_steering_angle = stabilize_steering_angle(curr_steering_angle, new_steering_angle, len(lane_lines))


    #driver.set_steering_angle(curr_steering_angle)
    driver.set_steering_angle(new_steering_angle)
    curr_heading_image = display_heading_line(frame, old_steering_angle)
    cv2.imwrite("heading.png", curr_heading_image)

    return curr_heading_image



#detects all red lines on image an turns it into two lanes
def detect_lane(frame):
    edges = detect_edges(frame) #detect the red borders of the track
    cv2.imwrite("edge.png", edges)
    cropped_edges = region_of_interest(edges) #only detects bottom side of the screen (no sky)
    cv2.imwrite("cropped_edges.png", cropped_edges)

    line_segments = detect_line_segments(cropped_edges) #marks all red lines in an image
    line_segment_image = display_lines(frame, line_segments) #display all detected red lines on image in green
    cv2.imwrite("line_segments.png", line_segment_image)

    lane_lines = average_slope_intercept(frame, line_segments) #This function combines line segments into one or two lane lines
    lane_lines_image = display_lines(frame, lane_lines) #display lane lines on image in green
    cv2.imwrite("lane_lines.png", lane_lines_image)
    return lane_lines, lane_lines_image
    
#detect the red borders of the track
def detect_edges(frame):
    # filter for red lane lines
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    cv2.imwrite("hsv.png", hsv)
    lower  = np.array([0, 70, 70])
    upper = np.array([30, 255, 255])
    # lower  = np.array([0, 70, 70])
    # upper = np.array([8, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    cv2.imwrite("mask.png", mask)

    # detect edges
    edges = cv2.Canny(mask, 200, 400)
    #cv2.imwrite("edge.png", edges)
    return edges

#only detects bottom side of the screen (no sky)
def region_of_interest(canny):
    height, width = canny.shape
    mask = np.zeros_like(canny)

    # only focus bottom half of the screen

    polygon = np.array([[
        (0, height * 1 / 2),
        (width, height * 1 / 2),
        (width, height),
        (0, height),
    ]], np.int32)

    cv2.fillPoly(mask, polygon, 255)
    #cv2.imwrite("cropped.png", mask)
    masked_image = cv2.bitwise_and(canny, mask)
    return masked_image

#marks all the (red)lines in an image
def detect_line_segments(cropped_edges):
    # tuning min_threshold, minLineLength, maxLineGap is a trial and error process by hand
    rho = 1  # precision in pixel, i.e. 1 pixel
    angle = np.pi / 180  # degree in radian, i.e. 1 degree
    min_threshold = 10  # minimal of votes
    line_segments = cv2.HoughLinesP(cropped_edges, rho, angle, min_threshold, np.array([]), minLineLength=8,
                                    maxLineGap=4) #HoughLinesP marks all the lines in an image

    if line_segments is not None:
        for line_segment in line_segments:
            logging.debug('detected line_segment:')
            logging.debug("%s of length %s" % (line_segment, length_of_line_segment(line_segment[0])))

    return line_segments

 
#This function combines line segments into one or two lane lines
#If all line slopes are < 0: then we only have detected left lane
#If all line slopes are > 0: then we only have detected right lane
def average_slope_intercept(frame, line_segments):
    lane_lines = []
    if line_segments is None:
        logging.info('No line_segment segments detected')
        return lane_lines

    height, width, _ = frame.shape
    left_fit = []
    right_fit = []

    boundary = 1/3
    left_region_boundary = width * (1 - boundary)  # left lane line segment should be on left 2/3 of the screen
    right_region_boundary = width * boundary # right lane line segment should be on left 2/3 of the screen

    for line_segment in line_segments:
        for x1, y1, x2, y2 in line_segment:
            if x1 == x2:
                #logging.info('skipping vertical line segment (slope=inf): %s' % line_segment)
                continue
            fit = np.polyfit((x1, x2), (y1, y2), 1)
            slope = fit[0]
            intercept = fit[1]
            if slope < 0:
                if x1 < left_region_boundary and x2 < left_region_boundary:
                    left_fit.append((slope, intercept))
            else:
                if x1 > right_region_boundary and x2 > right_region_boundary:
                    right_fit.append((slope, intercept))

    left_fit_average = np.average(left_fit, axis=0)
    if len(left_fit) > 0:
        lane_lines.append(make_points(frame, left_fit_average))

    right_fit_average = np.average(right_fit, axis=0)
    if len(right_fit) > 0:
        lane_lines.append(make_points(frame, right_fit_average))

    logging.debug('lane lines: %s' % lane_lines)  # [[[316, 720, 484, 432]], [[1009, 720, 718, 432]]]

    return lane_lines

#Find the steering angle based on lane line coordinate
#We assume that camera is calibrated to point to dead center
def compute_steering_angle(frame, lane_lines):
    if len(lane_lines) == 0:
        logging.info('No lane lines detected, do nothing')
        return -90

    height, width, _ = frame.shape
    if len(lane_lines) == 1:
        logging.debug('Only detected one lane line, just follow it. %s' % lane_lines[0])
        x1, _, x2, _ = lane_lines[0][0]
        x_offset = x2 - x1
    else:
        _, _, left_x2, _ = lane_lines[0][0]
        _, _, right_x2, _ = lane_lines[1][0]
        camera_mid_offset_percent = 0.02 # 0.0 means car pointing to center, -0.03: car is centered to left, +0.03 means car pointing to right
        mid = int(width / 2 * (1 + camera_mid_offset_percent))
        x_offset = (left_x2 + right_x2) / 2 - mid

    # find the steering angle, which is angle between navigation direction to end of center line
    y_offset = int(height / 2)

    angle_to_mid_radian = math.atan(x_offset / y_offset)  # angle (in radian) to center vertical line
    angle_to_mid_deg = int(angle_to_mid_radian * 180.0 / math.pi)  # angle (in degrees) to center vertical line
    #steering_angle_old = angle_to_mid_deg + 90  # this is the steering angle needed by picar front wheel
    steering_angle = ((angle_to_mid_deg + 90) * 0.01) - 0.9 # this is the steering angle needed by picar front wheel
    logging.info('Proposed angle: %s' % (steering_angle))
    return steering_angle

def compute_steering_angle_oldVersion(frame, lane_lines):
    if len(lane_lines) == 0:
        return -90

    height, width, _ = frame.shape
    if len(lane_lines) == 1:
        x1, _, x2, _ = lane_lines[0][0]
        x_offset = x2 - x1
    else:
        _, _, left_x2, _ = lane_lines[0][0]
        _, _, right_x2, _ = lane_lines[1][0]
        camera_mid_offset_percent = 0.02 # 0.0 means car pointing to center, -0.03: car is centered to left, +0.03 means car pointing to right
        mid = int(width / 2 * (1 + camera_mid_offset_percent))
        x_offset = (left_x2 + right_x2) / 2 - mid

    # find the steering angle, which is angle between navigation direction to end of center line
    y_offset = int(height / 2)

    angle_to_mid_radian = math.atan(x_offset / y_offset)  # angle (in radian) to center vertical line
    angle_to_mid_deg = int(angle_to_mid_radian * 180.0 / math.pi)  # angle (in degrees) to center vertical line
    steering_angle_old = angle_to_mid_deg + 90  # this is the steering angle needed by picar front wheel
    #logging.info('Proposed angle old: %s' % (steering_angle_old))
    return steering_angle_old

#  Using last steering angle to stabilize the steering angle
#  This can be improved to use last N angles, etc
#  if new angle is too different from current angle, only turn by max_angle_deviation degrees
# def stabilize_steering_angle(curr_steering_angle, new_steering_angle, num_of_lane_lines, max_angle_deviation_two_lines=5, max_angle_deviation_one_lane=1):
#     if num_of_lane_lines == 2:
#         # if both lane lines detected, then we can deviate more
#         max_angle_deviation = max_angle_deviation_two_lines
#     else:
#         # if only one lane detected, don't deviate too much
#         max_angle_deviation = max_angle_deviation_one_lane
    
#     angle_deviation = new_steering_angle - curr_steering_angle
#     if abs(angle_deviation) > max_angle_deviation:
#         stabilized_steering_angle = int(curr_steering_angle + max_angle_deviation * angle_deviation / abs(angle_deviation))
#     else:
#         stabilized_steering_angle = new_steering_angle
        
#     logging.info('Proposed angle: %s, stabilized angle: %s' % (new_steering_angle, stabilized_steering_angle))
#     return stabilized_steering_angle

############################
# Utility Functions
############################
#display lines on image
def display_lines(frame, lines, line_color=(0, 255, 0), line_width=10):
    line_image = np.zeros_like(frame)
    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                cv2.line(line_image, (x1, y1), (x2, y2), line_color, line_width)
    line_image = cv2.addWeighted(frame, 0.8, line_image, 1, 1)
    return line_image

#line where the car is heading to
def display_heading_line(frame, steering_angle, line_color=(0, 0, 255), line_width=5, ):
    heading_image = np.zeros_like(frame)
    height, width, _ = frame.shape

    # figure out the heading line from steering angle
    # heading line (x1,y1) is always center bottom of the screen
    # (x2, y2) requires a bit of trigonometry

    # Note: the steering angle of:
    # 0-89 degree: turn left
    # 90 degree: going straight
    # 91-180 degree: turn right 
    steering_angle_radian = steering_angle / 180.0 * math.pi
    x1 = int(width / 2)
    y1 = height
    x2 = int(x1 - height / 2 / math.tan(steering_angle_radian))
    y2 = int(height / 2)

    cv2.line(heading_image, (x1, y1), (x2, y2), line_color, line_width)
    heading_image = cv2.addWeighted(frame, 0.8, heading_image, 1, 1)

    return heading_image

#calculate length of line in graph
def length_of_line_segment(line):
    x1, y1, x2, y2 = line
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

#tool for average slope
def make_points(frame, line):
    height, width, _ = frame.shape
    slope, intercept = line
    y1 = height  # bottom of the frame
    y2 = int(y1 * 1 / 2)  # make points from middle of the frame down

    # bound the coordinates within the frame
    x1 = max(-width, min(2 * width, int((y1 - intercept) / slope)))
    x2 = max(-width, min(2 * width, int((y2 - intercept) / slope)))
    return [[x1, y1, x2, y2]]


# picam2 = Picamera2()
# picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1280, 720)}))
# picam2.start()

# while True:
#     im = cv2.blur(picam2.capture_array(),(7,7),cv2.BORDER_DEFAULT)
#     cv2.imwrite("camera.png", im)
#     detect_lane(im)
#     sleep(2)

def test_photo(file):
    combo_image = follow_lane(im)
    cv2.imwrite("road_with_lines.png", combo_image)


#Reset the hardware
def cleanup():
    logging.info('Stopping the car, resetting hardware.')
    driver.set_wheels_speed(0.0)
    driver.set_steering_angle(0.0)



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (960, 540)}))
    picam2.start()
    try:
        while True:
            im = cv2.blur(picam2.capture_array(),(7,7),cv2.BORDER_DEFAULT)
            
            follow_lane(im)
            driver.set_wheels_speed(0.18)
    except KeyboardInterrupt:
        print('interrupted!')
        cleanup()







