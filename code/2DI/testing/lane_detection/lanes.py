import cv2
import numpy as np

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder


def make_coordinates(image, line_parameters):
    slope, intercept = line_parameters
    y1 = image.shape[0]
    y2 = int(y1*(7.5/10))
    x1 = int((y1 - intercept)/slope)
    x2 = int((y2 - intercept)/slope)
    return np.array([x1 ,y1 ,x2, y2])

def average_slope_intercept(image, lines):
    left_fit=[]
    right_fit=[]
    for line in lines:
        x1, y1, x2, y2 = line.reshape(4)
        parameters = np.polyfit((x1,x2),(y1,y2), 1)
        slope = parameters[0]
        intercept = parameters[1]
        if slope < 0:
            left_fit.append((slope, intercept))
        else:
            right_fit.append((slope, intercept))
    left_fit_average = np.average(left_fit, axis=0)
    right_fit_average = np.average(right_fit, axis=0)
    left_line = make_coordinates(image, left_fit_average)
    right_line = make_coordinates(image, right_fit_average)
    return np.array([left_line, right_line])

def canny(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(hsv, cv2.COLOR_RGB2GRAY)
    cv2.imwrite("hsv.png", hsv)
    cv2.imwrite('resultGRAY.png',gray)
    canny = cv2.Canny(gray, 0, 50)
    return canny

def display_lines(image, lines):
    line_image = np.zeros_like(image)
    if lines is not None:
        for x1, y1, x2, y2 in lines:
            cv2.line(line_image, (x1,y1), (x2,y2), (255,0,255), 35)
    return line_image

def region_of_interest(image):
   height = image.shape[0]
   horizon = np.array([[(0, height), (3280, height) , (3280, 1900),(0, 1900)]], np.int32)
   mask = np.zeros_like(image)
   cv2.fillPoly(mask, horizon, 255)
   masked_image = cv2.bitwise_and(image,mask)
   return masked_image

# cv2.imwrite("orig.png", im)
# image = cv2.imread('orig.png')
# lane_image = np.copy(image)
# canny_image = canny(lane_image)
# cropped_image = region_of_interest(canny_image)
# lines = cv2.HoughLinesP(cropped_image, 4, np.pi/180, 200, np.array([]), minLineLength=45, maxLineGap=20)
# average_lines = average_slope_intercept(lane_image, lines)
# line_image = display_lines(lane_image, average_lines)
# combo_image = cv2.addWeighted(lane_image, 0.8, line_image, 1, 1)
# # cv2.imwrite("hsv.png", hsv)
# # cv2.imwrite('resultGRAY.png',gray)
# cv2.imwrite('resultCANNY.png',canny_image)
# cv2.imwrite('resultMASK.png',combo_image)

#cap = cv2.VideoCapture(-1)


try:
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (3280, 2464)}))
    picam2.start()
    while(True):
        frame = cv2.blur(picam2.capture_array(),(7,7),cv2.BORDER_DEFAULT)
        canny_image = canny(frame)
        cropped_image = region_of_interest(canny_image)
        lines = cv2.HoughLinesP(cropped_image, 4, np.pi/180, 200, np.array([]), minLineLength=45, maxLineGap=20)
        average_lines = average_slope_intercept(frame, lines)
        line_image = display_lines(frame, average_lines)
        combo_image = cv2.addWeighted(frame, 0.8, line_image, 1, 1)
        cv2.imwrite('resultMASK.png',combo_image)
except KeyboardInterrupt:
    print('stopped')