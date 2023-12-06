import paho.mqtt.client as mqtt
import time

SUCCESS_MESSAGE = "Success"

client = None
distance = "0.0"
connection_status = False
distance_update_status = 0

# 0. define callbacks - functions that run when events happen.
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    # reconnect then subscriptions will be renewed.
    client.subscribe('SoundDetection/distance', qos=1)
    global connection_status
    connection_status = True
    print("Connection returned result from app subscriber: "+str(rc))
    
# The callback of the client when it disconnects.
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print('Unexpected disconnect from app subscriber')
    else:
        print('Expected disconnect from app subscriber')

# The default message callback.
# (you can create separate callbacks per subscribed topic)
def on_message(client, userdata, message):
    print('Received message: "' + str(message.payload) + '" on topic "' +
        message.topic + '" with QoS ' + str(message.qos))
    global distance, distance_update_status
    distance = str(message.payload.decode("utf-8"))
    distance_update_status = 1

def app_client_initialize():
    # 1. create a client instance.
    global client
    client = mqtt.Client()

    # add additional client options (security, certifications, etc.)
    # many default options should be good to start off.
    # add callbacks to client.
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    # 2. connect to a broker using one of the connect*() functions.
    client.connect_async('test.mosquitto.org')
    client.loop_start()

    return True, SUCCESS_MESSAGE

def app_disconnect():
    client.loop_stop()
    client.disconnect()
    return True, SUCCESS_MESSAGE

def app_collect_data():
    global distance_update_status
    start_time = time.time()
    elapsed_time = 0.0
    while distance_update_status == 0 and elapsed_time <= 5.0:
        elapsed_time = time.time() - start_time
        continue
    if distance_update_status == 0 and elapsed_time > 5.0:
        return -1, "Time out for SoundDetection connection" 
    distance_update_status = 0
    return distance, SUCCESS_MESSAGE
