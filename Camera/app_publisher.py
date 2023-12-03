import paho.mqtt.client as mqtt

IMU_COMMUNICATION_TIMEOUT = 5.0
SUCCESS_MESSAGE = "Success"

client = None

# 0. define callbacks - functions that run when events happen.
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connection returned result from app publisher: "+str(rc))

# The callback of the client when it disconnects.
def on_disconnect(client, userdata, rc):
    if rc != 0:
        print('Unexpected disconnect from app publisher:')
    else:
        print('Expected disconnect from app publisher:')

# The default message callback.
# (you can create separate callbacks per subscribed topic)
def on_message(client, userdata, message):
    print('Received message: "' + str(message.payload) + '" on topic "' +
        message.topic + '" with QoS ' + str(message.qos))

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
    return True, SUCCESS_MESSAGE

def app_publish_data(data):
    global client
    if client is None:
        return False, "Camera: publisher client is None"
    # 3. call one of the loop*() functions to maintain network traffic flow with the broker.
    client.loop_start()
    info = client.publish('Camera/instruction', data, qos=1)
    # while not info.is_published():
    #     try:
    #         info.wait_for_publish(IMU_COMMUNICATION_TIMEOUT)
    #     except ValueError or RuntimeError:
    #         return False, "App: publisher failed to publish data"
    client.loop_stop()
    # use disconnect() to disconnect from the broker.
    # client.disconnect()
    return True, SUCCESS_MESSAGE

def app_disconnect():
    global client
    client.disconnect()
    return True, SUCCESS_MESSAGE
