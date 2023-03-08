import cv2
import numpy as np
import time
import math
from shooterdriver import ShooterDriver

driver = ShooterDriver()

def make_coordinates(image, line_parameters):
    slope, intercept = line_parameters
    y1 = image.shape[0]
    y2 = int(y1*(7/10))
    x1 = int((y1 - intercept)/slope)
    x2 = int((y2 - intercept)/slope)
    return np.array([x1 ,y1 ,x2, y2])

def average_slope_intercept(image, lines):
    try:
        left_line=[]
        right_line=[]
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
        if len(left_fit) > 0:
            left_line.append(make_coordinates(image, left_fit_average))
        if len(right_fit) > 0:
            right_line.append(make_coordinates(image, right_fit_average))
        return np.array([left_line, right_line])
    
    except Exception as e:
        print(f"error average slope: {e}")

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


def display_lines(image, lines, steering_angle):
    try:
        height, width, _ = image.shape
        line_image = np.zeros_like(image)
        if lines is not None:
            for line in lines:
                for x1, y1, x2, y2 in line:
                    cv2.line(line_image, (x1,y1), (x2,y2), (255,0,255), 5)

        # figure out the heading line from steering angle
        # heading line (x1,y1) is always center bottom of the screen
        # (x2, y2) requires a bit of trigonometry

        # Note: the steering angle of:
        # 0-89 degree: turn left
        # 90 degree: going straight
        # 91-180 degree: turn right 
        if steering_angle is not None:
            steering_angle_radian = float(steering_angle / 180.0 * math.pi)
        else:
            steering_angle_radian = float(90 / 180.0 * math.pi)
        x1 = int(width / 2)
        y1 = height
        x2 = int(x1 - height / 2 / float(math.tan(steering_angle_radian)))
        y2 = int(height / 1.5)


        cv2.line(line_image, (x1, y1), (x2, y2), (0,255,0), 5)
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

def compute_steering_angle(frame, lane_lines):
    try:
        if len(lane_lines[0]) == 0 and len(lane_lines[1]) == 0:
            return -90

        height, width, _ = frame.shape
        if len(lane_lines[0]) == 0 and len(lane_lines[1]) == 1:
            x1, _, x2, _ = lane_lines[1][0]
            x_offset = x2 - x1
        elif len(lane_lines[0]) == 1 and len(lane_lines[1]) == 0:
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
        steering_angle = angle_to_mid_deg + 90  # this is the steering angle to display
        #steering_angle = ((angle_to_mid_deg + 90) * 0.01) - 0.9 # this is the steering angle needed by picar front wheel
        return steering_angle
    except Exception as e:
        print(f"error steering: {e}")


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
    steering_angle = compute_steering_angle(frame, average_lines) # replace this with your steering angle calculation function
    print(steering_angle)
    line_image = display_lines(frame, average_lines, steering_angle)
    try:
        combo_image = cv2.addWeighted(frame, 0.8, line_image, 1, 1)
    except:
        print("failed to draw lines")
    new_steering_angle = (steering_angle * 0.01) - 0.9
    print(new_steering_angle)
    driver.set_steering_angle(new_steering_angle)
    driver.set_wheels_speed(0.05)
    print("--- %s seconds ---" % (time.time() - start_time))
    cv2.imwrite('./result.png',combo_image)