import cv2
import pandas as pd
from datetime import datetime
from threading import Thread
import subprocess


################### Raspberry Pi stream to Youtube ###################
    
if __name__ == "__main__":

    
    command = ['ffmpeg',
           '-re',
           '-ar', '44100',
           '-ac', '2',
           '-acodec', 'pcm_s16le',
           '-f', 's16le',
           '-ac', '2',
           '-f', 'alsa',
           '-i', 'plughw:1,0',
           '-itsoffset', '-2',
           '-i', '-',
           '-vcodec', 'copy',
           '-acodec', 'aac',
           '-ab', '384k',
           '-g', '17',
           '-strict', 'experimental',
           '-f', 'flv',
           'rtmp://a.rtmp.youtube.com/live2/bpug-8qbh-t98s-df6c-f8fp']  # Replace with your own stream key

    
    subprocess.run("raspivid -o - -t 0 -vf -hf -fps 60 -b 12000000 -rot 180 | ffmpeg -re -ar 44100 -ac 2 -acodec pcm_s16le -f s16le -ac 2 -f alsa -i plughw:1,0 -itsoffset -2 -i - -vcodec copy -acodec aac -ab 384k -g 17 -strict experimental -f flv rtmp://a.rtmp.youtube.com/live2/bpug-8qbh-t98s-df6c-f8fp",shell=True)
   