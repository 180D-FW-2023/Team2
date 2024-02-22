from dataclasses import dataclass
from matplotlib import animation
from scipy.interpolate import interp1d
import imufusion
import matplotlib.pyplot as pyplot
import numpy
import requests
import os
from io import StringIO

RASPBERRY_PI_IP = "192.168.137.14"  # Replace with the actual IP address of your Raspberry Pi
CSV_FILE_URL = f"http://{RASPBERRY_PI_IP}:8000/pet_movement.csv"


def generate_trajectory():
    csv_content = None
    response = None
    try:
        response = requests.get(CSV_FILE_URL, timeout=5)
    except requests.exceptions.Timeout:
        csv_content = "../IMU/plotting_test/pet_movement.csv"
    except requests.exceptions.ConnectionError:
        csv_content = "../IMU/plotting_test/pet_movement.csv"

    if response is None:
        csv_content = "../IMU/plotting_test/pet_movement.csv"
    elif response.status_code == 200:
        # Use numpy to parse the CSV content
        csv_content = StringIO(response.text)
    else:
        print(f"Failed to download CSV file. Status code: {response.status_code}")
        csv_content = "../IMU/plotting_test/pet_movement.csv"

    # Import sensor data 
    data = numpy.genfromtxt(csv_content, delimiter=",", skip_header=1)

    # data = numpy.genfromtxt("../IMU/plotting_test/pet_movement.csv", delimiter=",", skip_header=1)

    sample_rate = 10  # 10 Hz

    timestamp = data[:, 0]
    gyroscope = data[:, 1:4]
    accelerometer = data[:, 4:7]
    magnetometer = data[:, 7:10]

    # Instantiate AHRS algorithms
    offset = imufusion.Offset(sample_rate)
    ahrs = imufusion.Ahrs()

    ahrs.settings = imufusion.Settings(imufusion.CONVENTION_NWU,
                                    0.5,  # gain
                                    2000,  # gyroscope range
                                    10,  # acceleration rejection
                                    10,  # magnetic rejection
                                    5 * sample_rate)  # rejection timeout = 5 seconds

    # Process sensor data
    delta_time = numpy.diff(timestamp, prepend=timestamp[0])

    euler = numpy.empty((len(timestamp), 3))
    internal_states = numpy.empty((len(timestamp), 3))
    acceleration = numpy.empty((len(timestamp), 3))

    for index in range(len(timestamp)):
        gyroscope[index] = offset.update(gyroscope[index])

        ahrs.update(gyroscope[index], accelerometer[index], magnetometer[index], delta_time[index])
        #ahrs.update_no_magnetometer(gyroscope[index], accelerometer[index], delta_time[index])

        euler[index] = ahrs.quaternion.to_euler()

        ahrs_internal_states = ahrs.internal_states
        internal_states[index] = numpy.array([ahrs_internal_states.acceleration_error,
                                            ahrs_internal_states.accelerometer_ignored,
                                            ahrs_internal_states.acceleration_recovery_trigger])

        acceleration[index] = 9.81 * ahrs.earth_acceleration  # convert g to m/s/s

    # Identify moving periods
    is_moving = numpy.empty(len(timestamp))

    for index in range(len(timestamp)):
        is_moving[index] = numpy.sqrt(acceleration[index].dot(acceleration[index])) > 3  # threshold = 3 m/s/s

    margin = int(0.1 * sample_rate)  # 100 ms

    for index in range(len(timestamp) - margin):
        is_moving[index] = any(is_moving[index:(index + margin)])  # add leading margin

    for index in range(len(timestamp) - 1, margin, -1):
        is_moving[index] = any(is_moving[(index - margin):index])  # add trailing margin

    # Calculate velocity (includes integral drift)
    velocity = numpy.zeros((len(timestamp), 3))

    for index in range(len(timestamp)):
        if is_moving[index]:  # only integrate if moving
            velocity[index] = velocity[index - 1] + delta_time[index] * acceleration[index]

    # Find start and stop indices of each moving period
    is_moving_diff = numpy.diff(is_moving, append=is_moving[-1])


    @dataclass
    class IsMovingPeriod:
        start_index: int = -1
        stop_index: int = -1


    is_moving_periods = []
    is_moving_period = IsMovingPeriod()

    for index in range(len(timestamp)):
        if is_moving_period.start_index == -1:
            if is_moving_diff[index] == 1:
                is_moving_period.start_index = index

        elif is_moving_period.stop_index == -1:
            if is_moving_diff[index] == -1:
                is_moving_period.stop_index = index
                is_moving_periods.append(is_moving_period)
                is_moving_period = IsMovingPeriod()

    # Remove integral drift from velocity
    velocity_drift = numpy.zeros((len(timestamp), 3))

    for is_moving_period in is_moving_periods:
        start_index = is_moving_period.start_index
        stop_index = is_moving_period.stop_index

        t = [timestamp[start_index], timestamp[stop_index]]
        x = [velocity[start_index, 0], velocity[stop_index, 0]]
        y = [velocity[start_index, 1], velocity[stop_index, 1]]
        z = [velocity[start_index, 2], velocity[stop_index, 2]]

        t_new = timestamp[start_index:(stop_index + 1)]

        velocity_drift[start_index:(stop_index + 1), 0] = interp1d(t, x)(t_new)
        velocity_drift[start_index:(stop_index + 1), 1] = interp1d(t, y)(t_new)
        velocity_drift[start_index:(stop_index + 1), 2] = interp1d(t, z)(t_new)

    velocity = velocity - velocity_drift

    # Calculate position
    position = numpy.zeros((len(timestamp), 3))

    for index in range(len(timestamp)):
        position[index] = position[index - 1] + delta_time[index] * velocity[index]

    # Print error as distance between start and final positions
    print("Error: " + "{:.3f}".format(numpy.sqrt(position[-1].dot(position[-1]))) + " m")

    # create 3D plot
    if True:
        figure = pyplot.figure(figsize=(10, 10))

        axes = pyplot.axes(projection="3d")
        axes.set_xlabel("m")
        axes.set_ylabel("m")
        axes.set_zlabel("m")
        axes.set_title("Positions")
        portion = int(position.shape[0] * 0.8)

        x = position[:portion, 0]
        y = position[:portion, 1]
        z = position[:portion, 2]

        axes.set_xticks([])
        axes.set_yticks([])
        axes.set_zticks([])

        scatter = axes.scatter(x, y, x)
        figure.savefig("pet_movement.png", dpi=50)
        pyplot.close(figure)

