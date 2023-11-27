#!/usr/bin/python
#
#       This program is modified from Ozzmaker's official tutorial on BerryIMU
#       https://ozzmaker.com/accelerometer-to-g/

import time
import IMU
import sys
import math
import numpy as np
import imu_publisher
import imu_subscriber
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
from queue import Queue

# Hyperparameter
G_VALUE = 9.8067
Z_CALIBRATE = 1.02
Y_CALIBRATE = -0.017
X_CALIBRATE = 0.005
TIME_STAMP = 0.03
PASSING_THRESHOLD = 0.15

QUEUE_SIZE = 15
QUEUE_MAX_SIZE = 30

COVARIANCE_UNCERTAINTY = 100.0
MEASUREMENT_NOISE = 0.02
PROCESS_NOISE_VARIANCE = 0.02
KALMAN_LOW_PASS = 0.02

v_x_last = 0
v_y_last = 0
v_z_last = 0

x_pos = 0
y_pos = 0
z_pos = 0

distance = 0
kalman_distance = 0

publish_instruction = 0

# moving average filter
acc_x_queue = Queue(maxsize = QUEUE_MAX_SIZE)
acc_y_queue = Queue(maxsize = QUEUE_MAX_SIZE)
acc_z_queue = Queue(maxsize = QUEUE_MAX_SIZE)
acc_x_moving_sum = 0
acc_y_moving_sum = 0
acc_z_moving_sum = 0


def low_pass_filter(acc_x, acc_y, acc_z, filter = PASSING_THRESHOLD):
    if (abs(acc_x) < filter):
        acc_x = 0.0
    if (abs(acc_y) < filter):
        acc_y = 0.0
    if (abs(acc_z) < filter):
        acc_z = 0.0
    return acc_x, acc_y, acc_z

def moving_average(acc_x, acc_y, acc_z):
    acc_x_queue.put(acc_x)
    acc_y_queue.put(acc_y)
    acc_z_queue.put(acc_z)

    pop_x = acc_x_queue.get()
    pop_y = acc_y_queue.get()
    pop_z = acc_z_queue.get()

    global acc_x_moving_sum
    global acc_y_moving_sum
    global acc_z_moving_sum

    acc_x_moving_sum = acc_x_moving_sum - pop_x + acc_x
    acc_y_moving_sum = acc_y_moving_sum - pop_y + acc_y
    acc_z_moving_sum = acc_z_moving_sum - pop_z + acc_z

    return acc_x_moving_sum / QUEUE_SIZE, acc_y_moving_sum / QUEUE_SIZE, acc_z_moving_sum / QUEUE_SIZE

def calculate_distance(vel, acc):
    return vel * TIME_STAMP + 0.5 * acc * TIME_STAMP**2

def calculate_velocity(vel, acc):
    return vel + acc * TIME_STAMP

def initialize_kalman():
    kalman = KalmanFilter(dim_x=3, dim_z=1)
    # Acc, Vel, Pos
    kalman.x = np.array([0., 0., 0.])
    kalman.F = np.array([[1., 0., 0.],
                       [TIME_STAMP, 1., 0.],
                       [0.5 * (TIME_STAMP**2), TIME_STAMP, 0.]])
    
    kalman.H = np.array([[1., 0., 0.]])
    kalman.P *= COVARIANCE_UNCERTAINTY
    kalman.R = MEASUREMENT_NOISE

    kalman.Q = Q_discrete_white_noise(dim=3, dt=TIME_STAMP, var=PROCESS_NOISE_VARIANCE)   
    return kalman

##-------- INITIALIZATION PROCESS --------##
print("##-------- INITIALIZATION PROCESS STARTS--------##")

IMU.detectIMU()     #Detect if BerryIMU is connected.
if(IMU.BerryIMUversion == 99):
    print(" No BerryIMU found... exiting ")
    sys.exit()
IMU.initIMU()       #Initialise the accelerometer, gyroscope and compass

# prefill the queue
for i in range(QUEUE_SIZE):
    acc_x_queue.put(0)
    acc_y_queue.put(0)
    acc_z_queue.put(0)

# initialize kalman filter
kalman_x = initialize_kalman()
kalman_y = initialize_kalman()
kalman_z = initialize_kalman()

# initialize communication protocols
if not imu_publisher.imu_client_initialize():
    sys.exit("IMU: MQTT publisher failed to initialize")

if not imu_subscriber.imu_client_initialize():
    sys.exit("IMU: MQTT subscriber failed to initialize")

print("##-------- INITIALIZATION PROCESS ENDS--------##")
##-------- INITIALIZATION PROCESS --------##


while True:

    #Read the accelerometer,gyroscope and magnetometer values
    ACCx = IMU.readACCx()
    ACCy = IMU.readACCy()
    ACCz = IMU.readACCz()
    yG = (ACCx * 0.244)/1000
    xG = (ACCy * 0.244)/1000
    zG = (ACCz * 0.244)/1000

    # calibration (may remove this)
    acc_x = (xG - X_CALIBRATE) * G_VALUE
    acc_y = (yG - Y_CALIBRATE) * G_VALUE
    acc_z = (zG - Z_CALIBRATE) * G_VALUE

    # print(f"Recorded: x: {acc_x}, y: {acc_y}, z: {acc_z}")

    # low pass filter to denoise raw data
    acc_x, acc_y, acc_z = low_pass_filter(acc_x, acc_y, acc_z)

    # Kalman Filter
    # kalman_x.predict()
    # kalman_x.update(acc_x)
    # kalman_state_x = kalman_x.x
    # acc_x = kalman_state_x[0]

    # kalman_y.predict()
    # kalman_y.update(acc_y)
    # kalman_state_y = kalman_y.x
    # acc_y = kalman_state_y[0]

    # kalman_z.predict()
    # kalman_z.update(acc_z)
    # kalman_state_z = kalman_z.x
    # acc_z = kalman_state_z[0]

    # print(f"Kalman: x: {acc_x}, y: {acc_y}, z: {acc_z}")

    # kalman_distance += math.sqrt(kalman_state_x[2]**2 + kalman_state_y[2]**2 + kalman_state_z[2]**2)
    # print(f"Kalman distance: {kalman_distance} m")

    # moving average filter (replaced by Kalman in the future)
    acc_x, acc_y, acc_z = moving_average(acc_x, acc_y, acc_z)
    # another low pass filter to denoise the calculated data
    acc_x, acc_y, acc_z = low_pass_filter(acc_x, acc_y, acc_z, KALMAN_LOW_PASS)

    # resetting
    if (acc_x == 0):
        v_x_last = 0
        # kalman_x.x = np.array([0., 0., kalman_x.x[2]])
    if (acc_y == 0):
        v_y_last = 0
        # kalman_y.x = np.array([0., 0., kalman_y.x[2]])
    if (acc_z == 0):
        v_z_last = 0
        # kalman_z.x = np.array([0., 0., kalman_z.x[2]])
    

    x_distance = calculate_distance(v_x_last, acc_x)
    y_distance = calculate_distance(v_y_last, acc_y)
    z_distance = calculate_distance(v_z_last, acc_z)

    x_pos += x_distance
    y_pos += y_distance
    z_pos += z_distance

    distance += math.sqrt(x_distance**2 + y_distance**2 + z_distance**2)

    v_x_last = calculate_velocity(v_x_last, acc_x)
    v_y_last = calculate_velocity(v_y_last, acc_y)
    v_z_last = calculate_velocity(v_z_last, acc_z)

    # print(acc_x, acc_y, acc_z)
    # print(v_x_last, v_y_last, v_z_last)
    print(f"Current distance traveled: {distance} m")
    # print(f"x: {x_pos}, y: {y_pos}, z: {z_pos}")

    if imu_subscriber.get_imu_publish_instruction() == 1:
        imu_subscriber.reset_imu_publish_instruction()
        imu_publisher.imu_publish_data(distance)
        print("Data published")

    #slow program down a bit, makes the output more readable
    time.sleep(0.03)

