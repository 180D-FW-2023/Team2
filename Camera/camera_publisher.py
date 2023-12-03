import paho.mqtt.client as mqtt

Camera_COMMUNICATION_TIMEOUT = 5.0
SUCCESS_MESSAGE = "Success"

client = None

# 0. define callbacks - functions that run when events happen.
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connection returned result from Camera publisher: "+str(rc))

# The callback of the client when it disconnects.
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print('Unexpected disconnect from Camera publisher')
    else:
        print('Expected disconnect from Camera publisher')

# The default message callback.
# (you can create separate callbacks per subscribed topic)
def on_message(client, userdata, message):
    print('Received message: "' + str(message.payload) + '" on topic "' +
        message.topic + '" with QoS ' + str(message.qos))

def camera_client_initialize():
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
    return True, ""

def camera_publish_data(data):
    global client
    if client is None:
        return False, "Camera: publisher client is None"
    
    # publish Camera data to the broker
    client.loop_start()
    info = client.publish('Camera/distance', data, qos=1)
    # while not info.is_published():
    #     try:
    #         info.wait_for_publish(Camera_COMMUNICATION_TIMEOUT)
    #     except ValueError or RuntimeError:
    #         return False, "Camera: publisher failed to publish data"
    client.loop_stop()

    return True, SUCCESS_MESSAGE

def camera_client_disconnect():
    global client
    client.disconnect()
    return True, SUCCESS_MESSAGE
