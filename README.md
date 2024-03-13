# Team2
AIPet: automated smart pet monitor
## Camera:
- Install livestream packages by running:
  ```pip install -r requirements.txt```
- Video Live Streaming: ```python livestream.py```

## Microphone
- Input the email address that the user wished to be notified: ```nano sound.py```
- Run ```python sound.py```

## PhotoCapture:
The final version of Object Detection: 
- For environmental setup, follow the instructions in the file named terminal saved output in ObjectDetection_camera
- run object-ident_pet_video_capture.py

## IMU
### Directory Structure:
- \_\_init\_\_.py: python package indicator
- /plotting_test: testing files for IMU fusion algorithm
- calibrateBerrtIMU.py: calibration script for berry IMU, not neccessary but will improve accuracy
- plotIMU.py: IMU script for collecting IMU data and store them in a .csv file
- trajectory_generation.py: a function for generating trajectory data using IMU fusion

### Bootstrap process
Follow the instruction on: https://github.com/ozzmaker/BerryIMU. 
Install relative IMU packages 

In the project directory, run:

```
python IMU/berryIMU-measure-G.py
```

## User App
### Directory Structure:
- \_\_init\_\_.py: python package indicator
- main.py: main entrance for Tkinter GUI root module
- user_notification.py: function for sending out user notification through email

### Bootstrap process
In the project directory, run:

```
python user-app/main.py
```
