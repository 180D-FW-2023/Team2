# Team2
AIPet: automated smart pet monitor
## Camera:
- Install livestream packages by running:
  ```pip install -r requirements.txt```
- Video Live Streaming: ```python livestream.py```

## SoundDetection
### Directory Structure:
- dog_audio_classifier.ipynb: Google Colab notebook containing the dog bark audio classifier model, followed the tutorial from https://blog.tensorflow.org/2021/09/TinyML-Audio-for-everyone.html
- main.cpp: Modified inference-app/src/main.cpp from https://github.com/ArmDeveloperEcosystem/ml-audio-classifier-example-for-pico for additional communication function
- ml-audio-classifier-example-for-pico-dog_barks_2.tar.gz: Zip-file containing the training data used during Transfer Learning of the dog audio classifier 
- sent.py: Enable sending Gmail using the SMTP server
- sound.py: Notify the user once received signals from Raspberry Pi Pico suggesting that there is continuous dog bark in the board environment

### Bootstrap process:
- If you wish to train the ML model, download the dog_audio_classifier.ipynb and open it on Google Colab and run through each cell. Before the Inference Application, open up the file explorer UI pane located on the left-hand side of the Google Colab interface. Locate inference-app/src/main.cpp and replace it with the main.cpp file from the SoundDetection repository. Finish running all the cells. (Hardware: Raspberry Pi Pico)
- Change the email to the address you wish to be notified in sound.py line 25 , run ```nano SoundDetection/sound.py``` (Hardware: Raspberry Pi Zero)
- In the project directory, run ```python SoundDetection/sound.py``` (Hardware: Raspberry Pi Zero)

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
