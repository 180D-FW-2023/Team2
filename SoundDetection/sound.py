#!/usr/bin/python
from sent import send_simple_email
from savecsv import append_list_as_row
import RPi.GPIO as GPIO
import time
from datetime import datetime
import importlib.util



count = 0
last_bark_time = None

#GPIO SETUP
channel = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(channel, GPIO.IN)

def callback(channel):
        global count, last_bark_time
        count += 1
        if (count > 10):
                print( "Email sent!")
                #Put in your email address below ex: kuanghongchang@outlook.com
                send_simple_email("zhenbruin20@g.ucla.edu","Woof","Your dog is barking, you might want to check out the live stream?")
                #last_bark_time = datetime.now()
                #append_list_as_row('bark_file.csv', [last_bark_time])
                count = 0
        #if GPIO.input(channel):
                #print( "Your dog barked!")
                
        #else:
                #print( "Your dog barked!")

GPIO.add_event_detect(channel, GPIO.BOTH, bouncetime=800)  # let us know when the pin goes HIGH or LOW
GPIO.add_event_callback(channel, callback)  # assign function to GPIO PIN, Run function on change

# infinite loop
while True:
        time.sleep(1)
