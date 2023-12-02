import cv2
import time
import pandas as pd
from datetime import datetime
from threading import Thread
import camera_publisher
import camera_subscriber

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

################### Main function ###################

# Report to client app
def reportEating():
    if camera_subscriber.get_camera_publish_instruction() == 1:
        camera_subscriber.reset_camera_publish_instruction()
        publish_result, message = camera_publisher.camera_publish_data("Eating")
        if not publish_result:
            print(message)
        else:
            print("Data published: pet is eating")

# Detection 
def getObjects(img, thres, nms, draw=True, objects=[]):
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)
    objectInfo = []
    if len(objects) == 0: objects = classNames
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            if className in objects:
                objectInfo.append([box, className])
                if draw:
                    cv2.rectangle(img, box, color=(0, 255, 0), thickness=2)
                    cv2.putText(img, className.upper(), (box[0] + 10, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(img, str(round(confidence * 100, 2)), (box[0] + 200, box[1] + 30),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
    return img, objectInfo

# Recording 
pet_presence = {} # This is for tracking
recent_consistent_detections = {pet: 0 for pet in pets} # Handle the pet's sudden change with a buffer to account for detection instability
consistent_stay_detections = {pet: {obj: 0 for obj in item_objects} for pet in pets} # Same, but for stay detection

def update_pet_presence(objectInfo):
    current_time = time.time()
    detected_pets = [className for _, className in objectInfo if className in pets]
    detected_objects = [objName for _, objName in objectInfo if objName in item_objects]
    pet_status = {}
    
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
            # If time greater than 20 seconds, report to client-app once
            #elif pet_presence[pet]['buffer']==20:
                #reportEating()
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
    
    return pet_status

class VideoStreamWidget(object):
    def __init__(self, src=0):
        # Create a VideoCapture object
        self.capture = cv2.VideoCapture(src)

        # Start the thread to read frames from the video stream
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        # Read the next frame from the stream in a different thread
        while True:
            if self.capture.isOpened():
                (self.status, self.frame) = self.capture.read()

    def show_frame(self):
        # Display frames in main program
        if self.status:
            self.frame = self.maintain_aspect_ratio_resize(self.frame, width=600)
            cv2.imshow('IP Camera Video Streaming', self.frame)

        # Press Q on keyboard to stop recording
        key = cv2.waitKey(1)
        if key == ord('q'):
            self.capture.release()
            cv2.destroyAllWindows()
            exit(1)

    # Resizes a image and maintains aspect ratio
    def maintain_aspect_ratio_resize(self, image, width=None, height=None, inter=cv2.INTER_AREA):
        # Grab the image size and initialize dimensions
        dim = None
        (h, w) = image.shape[:2]

        # Return original image if no need to resize
        if width is None and height is None:
            return image

        # We are resizing height if width is none
        if width is None:
            # Calculate the ratio of the height and construct the dimensions
            r = height / float(h)
            dim = (int(w * r), height)
        # We are resizing width if height is none
        else:
            # Calculate the ratio of the 0idth and construct the dimensions
            r = width / float(w)
            dim = (width, int(h * r))

        # Return the resized image
        return cv2.resize(image, dim, interpolation=inter)
    

################### Stay detection ###################
if __name__ == "__main__":
    stream_link = 'http://131.179.33.111:8081/'
    video_stream_widget = VideoStreamWidget(stream_link)

    initialize_report()
    initialize_stay_report()  # Initialize pet stay report

    prev_frame_time = 0
    new_frame_time = 0
    while True:
        try:
            #video_stream_widget.show_frame()
            new_frame_time = time.time()

            success, img = video_stream_widget.status, video_stream_widget.frame
            if not success:
                raise ValueError("Failed to read frame from the camera.")
            #print("read from camera")

            result, objectInfo = getObjects(img, 0.45, 0.2, objects=objects)
            pet_status = update_pet_presence(objectInfo)
            #print("got objects and updated")

            
            y = 30
            for pet, status in pet_status.items():
                text = f"{pet}: {status}"
                cv2.putText(img, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                y += 30

            fps = 1 / (new_frame_time - prev_frame_time)
            prev_frame_time = new_frame_time
            fps_text = f"FPS: {int(fps)}"
            cv2.putText(img, fps_text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            cv2.imshow("Output", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
        except AttributeError:
            pass
    
    video_stream_widget.capture.release()
    cv2.destroyAllWindows()
    print("Camera released and windows closed.")
    
    '''

    cap = cv2.VideoCapture("test.mp4")
    #cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise ValueError("Failed to open the camera.")

    cap.set(3, 640)
    cap.set(4, 480)
    initialize_report()
    initialize_stay_report()  # Initialize pet stay report

    prev_frame_time = 0
    new_frame_time = 0

    while True:
        new_frame_time = time.time()

        success, img = cap.read()
        if not success:
            raise ValueError("Failed to read frame from the camera.")

        result, objectInfo = getObjects(img, 0.45, 0.2, objects=objects)
        pet_status = update_pet_presence(objectInfo)
        
        y = 30
        for pet, status in pet_status.items():
            text = f"{pet}: {status}"
            cv2.putText(img, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            y += 30

        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time
        fps_text = f"FPS: {int(fps)}"
        cv2.putText(img, fps_text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("Output", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        

    cap.release()
    cv2.destroyAllWindows()
    print("Camera released and windows closed.")
    '''