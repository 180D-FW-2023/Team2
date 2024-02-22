#!/bin/sh

virtualenv -p python3 .env
source .env/bin/activate
pip install requirements.txt
python3 object-ident_pet_video_capture.py 