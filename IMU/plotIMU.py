#!/usr/bin/python
#
#    This program  reads the angles from the acceleromteer, gyroscope
#    and mangnetometer on a BerryIMU connected to a Raspberry Pi.
#
#    This program includes two filters (low pass and median) to improve the
#    values returned from BerryIMU by reducing noise.
#
#    The BerryIMUv1, BerryIMUv2 and BerryIMUv3 are supported
#
#    This script is python 2.7 and 3 compatible
#
#    Feel free to do whatever you like with this code.
#    Distributed as-is; no warranty is given.
#
#    http://ozzmaker.com/


import sys
import time
import csv
import IMU
import time
import os
import http.server
import socketserver
import threading


RAD_TO_DEG = 57.29578
M_PI = 3.14159265358979323846
G_GAIN = 0.070          # [deg/s/LSB]  If you change the dps for gyro, you need to update this value accordingly
ACC_LPF_FACTOR = 0.4    # Low pass filter constant magnetometer
GYR_LPF_FACTOR = 0.4   # Low pass filter constant for accelerometer
MAG_LPF_FACTOR = 0.4
ACC_MEDIANTABLESIZE = 9         # Median filter table size for accelerometer. Higher = smoother but a longer delay
GYR_MEDIANTABLESIZE = 9         # Median filter table size for magnetometer. Higher = smoother but a longer 
MAG_MEDIANTABLESIZE = 9

# mag calibration
# magXmin =  -1239
# magYmin =  -4070
# magZmin =  164
# magXmax =  2733
# magYmax =  23
# magZmax =  4192

magXmin =  0
magYmin =  0
magZmin =  0
magXmax =  0
magYmax =  0
magZmax =  0

oldXGyrRawValue = 0
oldYGyrRawValue = 0
oldZGyrRawValue = 0
oldXAccRawValue = 0
oldYAccRawValue = 0
oldZAccRawValue = 0
oldXMagRawValue = 0
oldYMagRawValue = 0
oldZMagRawValue = 0

csv_file_name = "pet_movement.csv"
csv_fields = ["Time (s)", "Gyroscope X (deg/s)","Gyroscope Y (deg/s)","Gyroscope Z (deg/s)","Accelerometer X (g)","Accelerometer Y (g)","Accelerometer Z (g)", \
              "MagnetometerX", "MagnetometerY", "MagnetometerZ"]
csv_content = []

#Setup the tables for the mdeian filter. Fill them all with '1' so we dont get devide by zero error
acc_medianTable1X = [1] * ACC_MEDIANTABLESIZE
acc_medianTable1Y = [1] * ACC_MEDIANTABLESIZE
acc_medianTable1Z = [1] * ACC_MEDIANTABLESIZE
acc_medianTable2X = [1] * ACC_MEDIANTABLESIZE
acc_medianTable2Y = [1] * ACC_MEDIANTABLESIZE
acc_medianTable2Z = [1] * ACC_MEDIANTABLESIZE
gyr_medianTable1X = [1] * GYR_MEDIANTABLESIZE
gyr_medianTable1Y = [1] * GYR_MEDIANTABLESIZE
gyr_medianTable1Z = [1] * GYR_MEDIANTABLESIZE
gyr_medianTable2X = [1] * GYR_MEDIANTABLESIZE
gyr_medianTable2Y = [1] * GYR_MEDIANTABLESIZE
gyr_medianTable2Z = [1] * GYR_MEDIANTABLESIZE
mag_medianTable1X = [1] * MAG_MEDIANTABLESIZE
mag_medianTable1Y = [1] * MAG_MEDIANTABLESIZE
mag_medianTable1Z = [1] * MAG_MEDIANTABLESIZE
mag_medianTable2X = [1] * MAG_MEDIANTABLESIZE
mag_medianTable2Y = [1] * MAG_MEDIANTABLESIZE
mag_medianTable2Z = [1] * MAG_MEDIANTABLESIZE

PORT = 8000

# Function to serve the CSV file
def serve_csv():
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("Serving at port", PORT)
        httpd.serve_forever()


IMU.detectIMU()     #Detect if BerryIMU is connected.
if(IMU.BerryIMUversion == 99):
    print(" No BerryIMU found... exiting ")
    sys.exit()
IMU.initIMU()       #Initialise the accelerometer, gyroscope and compass

serve_csv_thread = threading.Thread(target=serve_csv, daemon=True)
serve_csv_thread.start()

start_time = time.time()
curr_time = 0.0

while True:
    csv_row = []

    #Read the accelerometer,gyroscope and magnetometer values
    ACCx = IMU.readACCx()
    ACCy = IMU.readACCy()
    ACCz = IMU.readACCz()
    GYRx = IMU.readGYRx()
    GYRy = IMU.readGYRy()
    GYRz = IMU.readGYRz()
    MAGx = IMU.readMAGx()
    MAGy = IMU.readMAGy()
    MAGz = IMU.readMAGz()

    #Apply compass calibration
    MAGx -= (magXmin + magXmax) /2
    MAGy -= (magYmin + magYmax) /2
    MAGz -= (magZmin + magZmax) /2

    ##Calculate current time
    curr_time = time.time() - start_time


    # ###############################################
    # #### Apply low pass filter ####
    # ###############################################
    GYRx =  GYRx  * GYR_LPF_FACTOR + oldXGyrRawValue*(1 - GYR_LPF_FACTOR);
    GYRy =  GYRy  * GYR_LPF_FACTOR + oldYGyrRawValue*(1 - GYR_LPF_FACTOR);
    GYRz =  GYRz  * GYR_LPF_FACTOR + oldZGyrRawValue*(1 - GYR_LPF_FACTOR);
    ACCx =  ACCx  * ACC_LPF_FACTOR + oldXAccRawValue*(1 - ACC_LPF_FACTOR);
    ACCy =  ACCy  * ACC_LPF_FACTOR + oldYAccRawValue*(1 - ACC_LPF_FACTOR);
    ACCz =  ACCz  * ACC_LPF_FACTOR + oldZAccRawValue*(1 - ACC_LPF_FACTOR);
    MAGx =  MAGx  * MAG_LPF_FACTOR + oldXMagRawValue*(1 - MAG_LPF_FACTOR);
    MAGy =  MAGy  * MAG_LPF_FACTOR + oldYMagRawValue*(1 - MAG_LPF_FACTOR);
    MAGz =  MAGz  * MAG_LPF_FACTOR + oldZMagRawValue*(1 - MAG_LPF_FACTOR);

    oldXGyrRawValue = GYRx
    oldYGyrRawValue = GYRy
    oldZGyrRawValue = GYRz
    oldXAccRawValue = ACCx
    oldYAccRawValue = ACCy
    oldZAccRawValue = ACCz
    oldXMagRawValue = MAGx
    oldYMagRawValue = MAGy
    oldZMagRawValue = MAGz

    # #########################################
    # #### Median filter for accelerometer ####
    # #########################################
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
    ACCx = acc_medianTable2X[int(ACC_MEDIANTABLESIZE/2)];
    ACCy = acc_medianTable2Y[int(ACC_MEDIANTABLESIZE/2)];
    ACCz = acc_medianTable2Z[int(ACC_MEDIANTABLESIZE/2)];

    # Convert acceleration to G
    yG = (ACCx * 0.244)/1000
    xG = (ACCy * 0.244)/1000
    zG = (ACCz * 0.244)/1000 

    # #########################################
    # #### Median filter for gyrometer ####
    # #########################################
    # cycle the table
    for x in range (GYR_MEDIANTABLESIZE-1,0,-1 ):
        gyr_medianTable1X[x] = gyr_medianTable1X[x-1]
        gyr_medianTable1Y[x] = gyr_medianTable1Y[x-1]
        gyr_medianTable1Z[x] = gyr_medianTable1Z[x-1]

    # Insert the latest values
    gyr_medianTable1X[0] = GYRx
    gyr_medianTable1Y[0] = GYRy
    gyr_medianTable1Z[0] = GYRz

    # Copy the tables
    gyr_medianTable2X = gyr_medianTable1X[:]
    gyr_medianTable2Y = gyr_medianTable1Y[:]
    gyr_medianTable2Z = gyr_medianTable1Z[:]

    # Sort table 2
    gyr_medianTable2X.sort()
    gyr_medianTable2Y.sort()
    gyr_medianTable2Z.sort()

    # The middle value is the value we are interested in
    GYRx = gyr_medianTable2X[int(GYR_MEDIANTABLESIZE/2)];
    GYRy = gyr_medianTable2Y[int(GYR_MEDIANTABLESIZE/2)];
    GYRz = gyr_medianTable2Z[int(GYR_MEDIANTABLESIZE/2)];

    #Convert Gyro raw to degrees per second
    rate_gyr_x =  GYRx * G_GAIN
    rate_gyr_y =  GYRy * G_GAIN
    rate_gyr_z =  GYRz * G_GAIN

    #########################################
    #### Median filter for magnetometer ####
    #########################################
    # cycle the table
    for x in range (MAG_MEDIANTABLESIZE-1,0,-1 ):
        mag_medianTable1X[x] = mag_medianTable1X[x-1]
        mag_medianTable1Y[x] = mag_medianTable1Y[x-1]
        mag_medianTable1Z[x] = mag_medianTable1Z[x-1]

    # Insert the latest values
    mag_medianTable1X[0] = MAGx
    mag_medianTable1Y[0] = MAGy
    mag_medianTable1Z[0] = MAGz

    # Copy the tables
    mag_medianTable2X = mag_medianTable1X[:]
    mag_medianTable2Y = mag_medianTable1Y[:]
    mag_medianTable2Z = mag_medianTable1Z[:]

    # Sort table 2
    mag_medianTable2X.sort()
    mag_medianTable2Y.sort()
    mag_medianTable2Z.sort()

    # The middle value is the value we are interested in
    MAGx = mag_medianTable2X[int(MAG_MEDIANTABLESIZE/2)];
    MAGy = mag_medianTable2Y[int(MAG_MEDIANTABLESIZE/2)];
    MAGz = mag_medianTable2Z[int(MAG_MEDIANTABLESIZE/2)];

    csv_row = [curr_time, rate_gyr_x, rate_gyr_y, rate_gyr_z, xG, yG, zG, MAGx, MAGy, MAGz]
    csv_content.append(csv_row)
    #print(f"Current time: {curr_time}, xG: {xG}, yG: {yG}, zG: {zG}, GyrX: {rate_gyr_x}, GyrY: {rate_gyr_y}, GyrZ: {rate_gyr_z}")

    #slow program down a bit, makes the output more readable
    #time.sleep(0.01)

    if (curr_time >= 30.0):
        print("Breaking loop")
        break

with open(csv_file_name, 'w') as csvfile:
    # creating a csv writer object
    csvwriter = csv.writer(csvfile)
    # writing the fields
    csvwriter.writerow(csv_fields)
    # writing the data rows
    csvwriter.writerows(csv_content)
    print("file saved!")

while True:
    pass