#!/usr/bin/python
#
#       This program is modified from Ozzmaker's official tutorial on BerryIMU
#       https://ozzmaker.com/accelerometer-to-g/

import time
import IMU
import sys
import math
import datetime
# import imu_publisher
# import imu_subscriber
from queue import Queue

# Hyperparameter for accelerometer
G_VALUE = 9.8067
Z_CALIBRATE = 0.0
Y_CALIBRATE = 0.0
X_CALIBRATE = 0.0
TIME_STAMP = 0.03
PASSING_THRESHOLD = 0.2

QUEUE_SIZE = 15
QUEUE_MAX_SIZE = 30

ACC_LOW_PASS = 0.2
VEL_LOW_PASS = 0.07

# Hyperparameter for gyroscope and magnetometer
RAD_TO_DEG = 57.29578
M_PI = 3.14159265358979323846
G_GAIN = 0.070          # [deg/s/LSB]  If you change the dps for gyro, you need to update this value accordingly
ACC_LPF_FACTOR = 0.4    # Low pass filter constant for accelerometer
ACC_MEDIANTABLESIZE = 9         # Median filter table size for accelerometer. Higher = smoother but a longer delay


#Kalman filter variables
Q_angle = 0.02
Q_gyro = 0.0015
R_angle = 0.005
y_bias = 0.0
x_bias = 0.0
XP_00 = 0.0
XP_01 = 0.0
XP_10 = 0.0
XP_11 = 0.0
YP_00 = 0.0
YP_01 = 0.0
YP_10 = 0.0
YP_11 = 0.0
KFangleX = 0.0
KFangleY = 0.0

def kalmanFilterY ( accAngle, gyroRate, DT):
    y=0.0
    S=0.0

    global KFangleY
    global Q_angle
    global Q_gyro
    global y_bias
    global YP_00
    global YP_01
    global YP_10
    global YP_11

    KFangleY = KFangleY + DT * (gyroRate - y_bias)

    YP_00 = YP_00 + ( - DT * (YP_10 + YP_01) + Q_angle * DT )
    YP_01 = YP_01 + ( - DT * YP_11 )
    YP_10 = YP_10 + ( - DT * YP_11 )
    YP_11 = YP_11 + ( + Q_gyro * DT )

    y = accAngle - KFangleY
    S = YP_00 + R_angle
    K_0 = YP_00 / S
    K_1 = YP_10 / S

    KFangleY = KFangleY + ( K_0 * y )
    y_bias = y_bias + ( K_1 * y )

    YP_00 = YP_00 - ( K_0 * YP_00 )
    YP_01 = YP_01 - ( K_0 * YP_01 )
    YP_10 = YP_10 - ( K_1 * YP_00 )
    YP_11 = YP_11 - ( K_1 * YP_01 )

    return KFangleY

def kalmanFilterX ( accAngle, gyroRate, DT):
    x=0.0
    S=0.0

    global KFangleX
    global Q_angle
    global Q_gyro
    global x_bias
    global XP_00
    global XP_01
    global XP_10
    global XP_11


    KFangleX = KFangleX + DT * (gyroRate - x_bias)

    XP_00 = XP_00 + ( - DT * (XP_10 + XP_01) + Q_angle * DT )
    XP_01 = XP_01 + ( - DT * XP_11 )
    XP_10 = XP_10 + ( - DT * XP_11 )
    XP_11 = XP_11 + ( + Q_gyro * DT )

    x = accAngle - KFangleX
    S = XP_00 + R_angle
    K_0 = XP_00 / S
    K_1 = XP_10 / S

    KFangleX = KFangleX + ( K_0 * x )
    x_bias = x_bias + ( K_1 * x )

    XP_00 = XP_00 - ( K_0 * XP_00 )
    XP_01 = XP_01 - ( K_0 * XP_01 )
    XP_10 = XP_10 - ( K_1 * XP_00 )
    XP_11 = XP_11 - ( K_1 * XP_01 )

    return KFangleX

gyroXangle = 0.0
gyroYangle = 0.0
gyroZangle = 0.0

kalmanX = 0.0
kalmanY = 0.0
oldXAccRawValue = 0
oldYAccRawValue = 0
oldZAccRawValue = 0
a = datetime.datetime.now()

#Setup the tables for the mdeian filter. Fill them all with '1' so we dont get devide by zero error
acc_medianTable1X = [1] * ACC_MEDIANTABLESIZE
acc_medianTable1Y = [1] * ACC_MEDIANTABLESIZE
acc_medianTable1Z = [1] * ACC_MEDIANTABLESIZE
acc_medianTable2X = [1] * ACC_MEDIANTABLESIZE
acc_medianTable2Y = [1] * ACC_MEDIANTABLESIZE
acc_medianTable2Z = [1] * ACC_MEDIANTABLESIZE

# Velocity
v_x_last = 0
v_y_last = 0
v_z_last = 0

# Position
x_pos = 0
y_pos = 0
z_pos = 0

# Distance
distance = 0

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

# initialize communication protocols
# if not imu_publisher.imu_client_initialize():
#     sys.exit("IMU: MQTT publisher failed to initialize")

# if not imu_subscriber.imu_client_initialize():
#     sys.exit("IMU: MQTT subscriber failed to initialize")

print("##-------- INITIALIZATION PROCESS ENDS--------##")
##-------- INITIALIZATION PROCESS --------##


while True:

    #Read the accelerometer,gyroscope and magnetometer values
    ACCx = IMU.readACCx()
    ACCy = IMU.readACCy()
    ACCz = IMU.readACCz()
    GYRx = IMU.readGYRx()
    GYRy = IMU.readGYRy()
    GYRz = IMU.readGYRz()

    ##Calculate loop Period(LP). How long between Gyro Reads
    b = datetime.datetime.now() - a
    a = datetime.datetime.now()
    LP = b.microseconds/(1000000*1.0)
    outputString = "Loop Time %5.2f " % ( LP )

    ###############################################
    #### Apply low pass filter ####
    ###############################################
    ACCx =  ACCx  * ACC_LPF_FACTOR + oldXAccRawValue*(1 - ACC_LPF_FACTOR)
    ACCy =  ACCy  * ACC_LPF_FACTOR + oldYAccRawValue*(1 - ACC_LPF_FACTOR)
    ACCz =  ACCz  * ACC_LPF_FACTOR + oldZAccRawValue*(1 - ACC_LPF_FACTOR)

    oldXAccRawValue = ACCx
    oldYAccRawValue = ACCy
    oldZAccRawValue = ACCz

    #########################################
    #### Median filter for accelerometer ####
    #########################################
    # cycle the table
    for x in range (ACC_MEDIANTABLESIZE-1,0,-1 ):
        acc_medianTable1X[x] = acc_medianTable1X[x-1]
        acc_medianTable1Y[x] = acc_medianTable1Y[x-1]
        acc_medianTable1Z[x] = acc_medianTable1Z[x-1]

    # Insert the lates values
    acc_medianTable1X[0] = ACCx
    acc_medianTable1Y[0] = ACCy
    acc_medianTable1Z[0] = ACCz

    # Copy the tables
    acc_medianTable2X = acc_medianTable1X[:]
    acc_medianTable2Y = acc_medianTable1Y[:]
    acc_medianTable2Z = acc_medianTable1Z[:]

    # Sort table 2
    acc_medianTable2X.sort()
    acc_medianTable2Y.sort()
    acc_medianTable2Z.sort()

    # The middle value is the value we are interested in
    ACCx = acc_medianTable2X[int(ACC_MEDIANTABLESIZE/2)]
    ACCy = acc_medianTable2Y[int(ACC_MEDIANTABLESIZE/2)]
    ACCz = acc_medianTable2Z[int(ACC_MEDIANTABLESIZE/2)]

    #Convert Gyro raw to degrees per second
    rate_gyr_x =  GYRx * G_GAIN
    rate_gyr_y =  GYRy * G_GAIN
    rate_gyr_z =  GYRz * G_GAIN

    #Convert Accelerometer values to degrees
    AccXangle =  (math.atan2(ACCy,ACCz)*RAD_TO_DEG)
    AccYangle =  (math.atan2(ACCz,ACCx)+M_PI)*RAD_TO_DEG

    #Change the rotation value of the accelerometer to -/+ 180 and
    #move the Y axis '0' point to up.  This makes it easier to read.
    if AccYangle > 90:
        AccYangle -= 270.0
    else:
        AccYangle += 90.0

    #Kalman filter used to combine the accelerometer and gyro values.
    kalmanY = kalmanFilterY(AccYangle, rate_gyr_y,LP)
    kalmanX = kalmanFilterX(AccXangle, rate_gyr_x,LP)

    print (f"Angle: x: {int(kalmanX)}, y: {int(kalmanY)}")

    yG = (ACCx * 0.244)/1000
    xG = (ACCy * 0.244)/1000
    zG = (ACCz * 0.244)/1000

    # calibration (may remove this)
    acc_x = (xG - X_CALIBRATE) * G_VALUE
    acc_y = (yG - Y_CALIBRATE) * G_VALUE
    acc_z = (zG - Z_CALIBRATE) * G_VALUE

    # conversion to real axis


    # low pass filter to denoise raw data
    acc_x, acc_y, acc_z = low_pass_filter(acc_x, acc_y, acc_z)

    print(f"Recorded: x: {acc_x:.2f}, y: {acc_y:.2f}, z: {acc_z:.2f}")

    # moving average filter (replaced by Kalman in the future)
    acc_x, acc_y, acc_z = moving_average(acc_x, acc_y, acc_z)
    # another low pass filter to denoise the calculated data
    acc_x, acc_y, acc_z = low_pass_filter(acc_x, acc_y, acc_z, ACC_LOW_PASS)

    # resetting
    if (acc_x == 0):
        v_x_last = 0
    if (acc_y == 0):
        v_y_last = 0
    if (acc_z == 0):
        v_z_last = 0  

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
    v_x_last, v_y_last, v_z_last = low_pass_filter(v_x_last, v_y_last, v_z_last, VEL_LOW_PASS)

    # print(acc_x, acc_y, acc_z)
    # print(v_x_last, v_y_last, v_z_last)
    # print(f"Current distance traveled: {distance}m")
    # print(f"x: {x_pos}, y: {y_pos}, z: {z_pos}")

    # if imu_subscriber.get_imu_publish_instruction() == 1:
    #     imu_subscriber.reset_imu_publish_instruction()
    #     publish_result, message = imu_publisher.imu_publish_data(distance)
    #     if not publish_result:
    #         print(message)
    #     else:
    #         print("Data published")

    #slow program down a bit, makes the output more readable
    time.sleep(0.03)

