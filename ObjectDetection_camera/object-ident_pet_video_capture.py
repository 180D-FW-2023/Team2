import cv2
import time
import pandas as pd
import numpy as np
from datetime import datetime
from collections import deque
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import extract_features
import config
import threading
from queue import Queue
import torch
from cap_from_youtube import cap_from_youtube
from vidgear.gears import CamGear
from openai import OpenAI

# Load image caption model
model = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
feature_extractor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Def caption function
max_length = 16
num_beams = 1
gen_kwargs = {"max_length": max_length, "num_beams": num_beams}
def predict_caption(image):
    # Make sure image is RGB not BGR

  pixel_values = feature_extractor(images=image, return_tensors="pt").pixel_values
  pixel_values = pixel_values.to(device)

  output_ids = model.generate(pixel_values, **gen_kwargs)

  preds = tokenizer.batch_decode(output_ids, skip_special_tokens=True)
  preds = [pred.strip() for pred in preds]
  return preds

# Load class names
classNames = []
classFile = "coco.names"
with open(classFile, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

# Load model configuration and weights
configPath = "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "frozen_inference_graph.pb"
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Define objects to detect
pets = ["cat", "dog", "bird"]
tables = ["dining table", 'desk']
bowls = ["bowl"]
chairs = ["chair", "couch"]
pet_home = ["bed"]
bed = ['bed']
objects = list(set(pets + tables + bowls + chairs + pet_home))
item_objects = list(set(tables + bowls + chairs + pet_home))

# Initialize report variables
current_report_date = None
report_filename = None

pet_stay_time = {pet: {obj: 0 for obj in objects} for pet in pets}
pet_stay_report_filename = None

################### Eating detection report ###################
def initialize_report():
    global current_report_date, report_filename
    current_report_date = datetime.now().date()
    report_filename = f"pet_eating_report_{current_report_date}.csv"
    pd.DataFrame(columns=['Time Entered', 'Time Left', 'Event']).to_csv(report_filename, index=False)

def add_info_to_report(info):
    global current_report_date, report_filename
    today = datetime.now().date()
    if today != current_report_date:
        initialize_report()  # Create new report for a new day
    report_df = pd.read_csv(report_filename)
    report_df = report_df.append(info, ignore_index=True)
    report_df.to_csv(report_filename, index=False)

################### Staying detection report ###################
def initialize_stay_report():
    global pet_stay_report_filename
    current_report_date = datetime.now().date()
    pet_stay_report_filename = f"pet_stay_report_{current_report_date}.csv"
    pd.DataFrame(columns=['Pet', 'Object with Most Stay']).to_csv(pet_stay_report_filename, index=False)

def update_stay_report():
    global pet_stay_report_filename
    today = datetime.now().date()
    if today != datetime.strptime(pet_stay_report_filename.split('_')[-1].split('.')[0], "%Y-%m-%d").date():
        initialize_stay_report()  # Create new report for a new day
    stay_report_df = pd.DataFrame(columns=['Pet', 'Object with Most Stay'])

    for pet in pet_presence:
        # Find the object with the maximum stay time for each pet
        if pet in pet_stay_time:
            most_stay_object = max(pet_stay_time[pet], key=pet_stay_time[pet].get)
            stay_report_df = stay_report_df.append({'Pet': pet, 'Object with Most Stay': most_stay_object}, ignore_index=True)
        
    stay_report_df.to_csv(pet_stay_report_filename, index=False)
    
################### Video caption report ###################
def initialize_caption_report():
    global current_report_date, caption_report_filename
    current_report_date = datetime.now().date()
    caption_report_filename = f"pet_video_captin_report_{current_report_date}.csv"
    pd.DataFrame(columns=['Time', 'Caption']).to_csv(caption_report_filename, index=False)

def add_info_to_caption_report(info):
    global current_report_date, caption_report_filename
    today = datetime.now().date()
    if today != current_report_date:
        initialize_report()  # Create new report for a new day
    report_df = pd.read_csv(caption_report_filename)
    report_df = report_df.append(info, ignore_index=True)
    report_df.to_csv(caption_report_filename, index=False)
################### Main function ###################

# Detection 
def getObjects(img, thres, nms, draw=True, objects=[]):
    imgShow = np.array(img)
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)
    objectInfo = []
    if len(objects) == 0: objects = classNames
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            if className in objects:
                objectInfo.append([box, className])
                if draw:
                    cv2.rectangle(imgShow, box, color=(0, 255, 0), thickness=2)
                    cv2.putText(imgShow, className.upper(), (box[0] + 10, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(imgShow, str(round(confidence * 100, 2)), (box[0] + 200, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
    return img, imgShow, objectInfo

# Recording 
pet_presence = {} # This is for tracking
recent_consistent_detections = {pet: 0 for pet in pets} # Handle the pet's sudden change with a buffer to account for detection instability
consistent_stay_detections = {pet: {obj: 0 for obj in item_objects} for pet in pets} # Same, but for stay detection

def update_pet_presence(objectInfo):
    current_time = time.time()
    detected_pets = [className for _, className in objectInfo if className in pets]
    detected_objects = [objName for _, objName in objectInfo if objName in item_objects]
    pet_status = {}
    eating_time = 0
    # Detect eating
    for pet in pets:
        is_pet_detected = pet in detected_pets
        is_pet_tracked = pet in pet_presence

        if is_pet_detected:
            # If detect pet, counting frame add 1
            recent_consistent_detections[pet] += 1
            
            # Consisitent thershold: 20
            if recent_consistent_detections[pet] < 20:
                continue
            
            # Reset other pet situation
            for other_pet in pets:
                if other_pet != pet:
                    recent_consistent_detections[other_pet] = 0
                    
            if not is_pet_tracked:
                # Reset consistent countings if it's not detected 
                recent_consistent_detections[pet] = 0
                
                # Initialize pet presence for newly detected pets
                pet_presence[pet] = {'first_seen': current_time, 'last_seen': current_time, 'buffer': 0}
                pet_status[pet] = 'Entered'
            else:
                # Update pet presence for already detected pets
                pet_presence[pet]['last_seen'] = current_time
                pet_presence[pet]['buffer'] = 0

            # If the pet has been detected long enough to be recorded
            eating_time = current_time - pet_presence[pet]['first_seen']
            pet_status[pet] = f'Detected for {int(eating_time)} seconds | Recorded' if eating_time > 30 else f'Detected for {int(eating_time)} seconds'

        elif is_pet_tracked:
            # Handle the pet's disappearance with a buffer to account for detection instability
            if pet_presence[pet]['buffer'] < 20:
                pet_presence[pet]['buffer'] += 1
            else:
                # Record and report pet's total presence time
                elapsed_time = current_time - pet_presence[pet]['first_seen']
                if elapsed_time > 30:
                    add_info_to_report({
                        'Time Entered': datetime.fromtimestamp(pet_presence[pet]['first_seen']).strftime('%Y-%m-%d %H:%M:%S'),
                        'Time Left': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Event': f'{pet} stayed for {int(elapsed_time)} seconds'
                    })
                del pet_presence[pet]
                pet_status[pet] = 'Left'
                
    # Detect staying                
    for pet in detected_pets:
        for objName in detected_objects:
            consistent_stay_detections[pet][objName] += 1
            if consistent_stay_detections[pet][objName] < 20:
                continue
            # update_pet_stay_time
            pet_stay_time[pet][objName] += time.time() - current_time
            for other_obj in item_objects:
                if other_obj != objName:
                    consistent_stay_detections[pet][other_obj] = 0

    update_stay_report()
    
    return pet_status, eating_time

def generate_caption(frames_queue, caption_queue, predict_caption):
    while True:
        cur_frame, record_prev, eating_time = frames_queue.get()
        if cur_frame is None:  
            break

        caption = predict_caption(cur_frame)[0]

        add_info_to_caption_report({
                    'Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Caption': caption,
                })
        caption_queue.put((caption, eating_time, eating_time))
        
################### Stay detection ###################
if __name__ == "__main__":

    # stream from youtube live
    stream = CamGear(source='https://www.youtube.com/watch?v=a2aX3RGRWSg', stream_mode = True, logging=True).start()

    # chatgpt output
    client = OpenAI()
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
        {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
    ]
    )

    print(completion.choices[0].message)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise ValueError("Failed to open the camera.")

    cap.set(3, 640)
    cap.set(4, 480)
    initialize_report()
    initialize_stay_report()
    initialize_caption_report()
    
    prev_frame_time = 0
    new_frame_time = 0
    caption = None
    frames = []
    record_prev = 0

    frames_queue = Queue()
    caption_queue = Queue()

    caption_thread = threading.Thread(target=generate_caption, args=(frames_queue, caption_queue, predict_caption))
    caption_thread.start()

    while True:
        
        new_frame_time = time.time()

        img = stream.read()
        if img is None:
            raise ValueError("Failed to read frame from the youtube.")

        #success, img = cap.read()
        #if not success:
            #raise ValueError("Failed to read frame from the camera.")

        ori_img, img_bbox, objectInfo = getObjects(img, 0.45, 0.2, objects=objects)
        pet_status, eating_time = update_pet_presence(objectInfo)

        y = 30
        for pet, status in pet_status.items():
            text = f"{pet}: {status}"
            cv2.putText(img_bbox, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            y += 30

        record_cur = eating_time - record_prev
        if record_cur < 0 or eating_time == 0:
            record_prev = 0
            caption = None
            
        if record_cur > 3:

            if record_cur >= 30:
                cur_frame = img.copy()
                frames_queue.put((cur_frame, record_prev, eating_time))
                cur_frame = None
                record_prev = eating_time
                
        if not caption_queue.empty():
            caption, record_prev, eating_time = caption_queue.get()

        if caption:
            cv2.putText(img_bbox, caption, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            y += 30

        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time
        fps_text = f"FPS: {int(fps)}"
        cv2.putText(img_bbox, fps_text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("Output", img_bbox)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        

    frames_queue.put((None, None, None))  
    caption_thread.join()  

    cap.release()
    cv2.destroyAllWindows()
    print("Camera released and windows closed.")