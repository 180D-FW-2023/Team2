import app_subscriber
import app_publisher


def initialize_app_subscriber():
    app_client_initialize_success, message = app_subscriber.app_client_initialize()
    return app_client_initialize_success, message

def initialize_app_publisher():
    app_client_initialize_success, message = app_publisher.app_client_initialize()
    return app_client_initialize_success, message

def disconnect_app_subscriber():
    app_client_disconnect_success, message = app_subscriber.app_disconnect()
    return app_client_disconnect_success, message

def disconnect_app_publisher():
    app_client_disconnect_success, message = app_publisher.app_disconnect()
    return app_client_disconnect_success, message

def get_imu_distance():
    app_publish_data_success, message = app_publisher.app_publish_data(1)
    if not app_publish_data_success:
        return 0, app_publish_data_success, message
    distance = app_subscriber.app_collect_data()
    return distance, app_publish_data_success, message