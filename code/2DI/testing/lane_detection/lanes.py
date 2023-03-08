import cv2
import numpy as np
import time
import math
from shooterdriver import ShooterDriver

driver = ShooterDriver()

def make_coordinates(image, line_parameters):
    # if (line_parameters[0] < 3.0e-10 and line_parameters[1] > 1.00000000e+01) or (line_parameters[0] > 3.0e-10 and line_parameters[1] < 1.00000000e+01):
    slope, intercept = line_parameters
    y1 = image.shape[0]
    y2 = int(y1*(7/10))
    x1 = int((y1 - intercept)/slope)
    x2 = int((y2 - intercept)/slope)
    return np.array([x1 ,y1 ,x2, y2])


def average_slope_intercept(image, lines):
    left_line=[]
    right_line=[]
    left_fit=[]
    right_fit=[]
    
    height, width, _ = image.shape

    left_boundary = width  # left lane line segment should be on left 2/3 of the screen
    right_boundary = 0 # right lane line segment should be on left 2/3 of the screen


    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line.reshape(4)
            parameters = np.polyfit((x1,x2),(y1,y2), 1)
            slope = parameters[0]
            intercept = parameters[1]
            if slope < 0:
                if (x1 < left_boundary and x2 < left_boundary):
                    left_fit.append((slope, intercept))
            else:
                if (x1 > right_boundary and x2 > right_boundary):
                    right_fit.append((slope, intercept))
    left_fit_average = np.average(left_fit, axis=0)
    right_fit_average = np.average(right_fit, axis=0)
    if len(left_fit) > 0:
        left_line.append(make_coordinates(image, left_fit_average))
    if len(right_fit) > 0:
        right_line.append(make_coordinates(image, right_fit_average))
        
    return np.array([left_line, right_line])

def canny(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower  = np.array([160, 80, 80]) #Color range grade (160-240 is blue) , Saturation, Value
    upper = np.array([200, 255, 255])
    gray = cv2.inRange(hsv, lower, upper)
    # cv2.imwrite("gray.png", gray)
    # gray2 = cv2.cvtColor(gray, cv2.COLOR_RGB2GRAY)
    # cv2.imwrite("hsv.png", hsv)
    #cv2.imwrite('./resultGRAY.png',gray2)
    canny = cv2.Canny(gray, 190, 255)
    cv2.imwrite('./resultCanny.png',canny)
    return canny


def display_lines(image, lines):
    print("line ", lines)
    try:
        height, width, _ = image.shape
        line_image = np.zeros_like(image)
        if lines is not None:
            for line in lines:
                for x1, y1, x2, y2 in line:
                    cv2.line(line_image, (int(x1),int(y1)), (int(x2),int(y2)), (255,0,255), 5)
        return line_image
    except Exception as e:
        print(e)


def region_of_interest(image):
   height = image.shape[0] 
   horizon = np.array([[(0, height), (320, height) , (320, height-50), (185, 120),(135, 120), (0, height-50)]], np.int32)
   mask = np.zeros_like(image)
   cv2.fillPoly(mask, horizon, 255)
   masked_image = cv2.bitwise_and(image,mask)
   cv2.imwrite('./resultROI.png',masked_image)
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

#


cap = cv2.VideoCapture(-1)
cap.set(cv2.CAP_PROP_FPS, 15)
fps = int(cap.get(5))
print("fps:", fps)
cap.set(3,320)
cap.set(4,240)
while(cap.isOpened()):
    start_time = time.time()
    _, frame = cap.read()
    canny_image = canny(frame)
    cropped_image = region_of_interest(canny_image)
    lines = cv2.HoughLinesP(cropped_image, 4, np.pi/180, 70, np.array([]), minLineLength=15, maxLineGap=4)
    average_lines = average_slope_intercept(frame, lines)
    try:
        line_image = display_lines(frame, average_lines)
        combo_image = cv2.addWeighted(frame, 0.8, line_image, 1, 1)
    except:
        print("can't draw lanes")
    print("--- %s seconds ---" % (time.time() - start_time))
    cv2.imwrite('./result.png',combo_image)