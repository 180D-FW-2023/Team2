# Team2
AIPet: automated smart pet monitor
## Camera:
Video Live Streaming: run object-ident_pet.py

## ObjectDetection:
Object Detection: run object-ident_pet.py

## VideoCapture:
The final version of Object Detection: 
- For environmental setup, follow the instructions on the URL:https://github.com/Shreyz-max/Video-Captioning?tab=readme-ov-file
- run object-ident_pet_video_capture.py

## IMU
### Directory Structure:
- \_\_init\_\_.py: python package indicator
- app_publisher.py: user application MQTT publisher functions (TBD: refactor to user-app) 
- app_subscriber.py: user application MQTT subscriber functions (TBD: refactor to user-app) 
- berryIMU-measure-G.py: IMU distance data processing logic
- imu_communication_api.py: communication with IMU api gateway
- imu_publisher.py: IMU MQTT publisher functions 
- imu_subscriber.py: IMU MQTT subscriber functions 

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
