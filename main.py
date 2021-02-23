import datetime
import json

import eventlet
from crccheck.checksum import Checksum8
from flask import Flask, render_template, request, jsonify
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap
import requests

eventlet.monkey_patch()

TURN_ON = "68 14 0D 33 37 3D 33 33 45 00 DE 87 86 74 78 33"
TURN_OFF = "68 14 0D 33 37 3D 33 33 45 00 DE 87 86 74 78 34"
RECHARGE = "68 14 10 33 34 3D 33 33 45 00 DE 87 86 74 78"
BALANCE = "68 11 04 33 34 C3 33"
CLEAR_BALANCE = "68 14 0D 33 36 3D 33 33 45 00 DE 87 86 74 78 34"
PREPAID = "68 14 0D 33 35 3D 33 33 45 00 DE 87 86 74 78 34"
POSTPAID = "68 14 0D 33 35 3D 33 33 45 00 DE 87 86 74 78 33"
PREPAID_BALANCE = "68 11 04 33 34 C3 33"

PREPAID_BALANCE_RESPONSE = "68 91 08 33 34 C3 33"
POSTPAID_BALANCE = "68 11 04 33 33 34 33"
POSTPAID_BALANCE_RESPONSE = "68 91 08 33 33 34 33"
END = "16"

app = Flask(__name__)
app.config['SECRET'] = 'my secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = 'localhost'  # use the free broker from HIVEMQ
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
app.config['MQTT_USERNAME'] = 'bigmachini'  # set the username here if you need authentication for the broker
app.config['MQTT_PASSWORD'] = 'Qwerty123.'  # set the password here if the broker demands authentication
app.config['MQTT_KEEPALIVE'] = 60  # set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes
app.config['MQTT_CLEAN_SESSION'] = True

mqtt = Mqtt(app)
socketio = SocketIO(app)
bootstrap = Bootstrap(app)

PUB_TOPIC_CONFIG = 'home_auto/config'
PUB_TOPIC_RELAY = 'home_auto/relay'
PUB_TOPIC_UPDATE = 'home_auto/update'
PUB_TOPIC_STATUS = 'home_auto/status'


@app.route('/', methods=['POST', 'GET'])
def sessions():
    return render_template('session.html')


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')


@socketio.on('my_event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    json['color'] = '#00FF00'
    socketio.emit('device_output', json, callback=messageReceived)


def publish_to_web(msg, topic):
    _msg = {
        'timestamp': str(datetime.datetime.now()),
        'topic': topic,
        'message': msg,
        'color': '#FF0000'
    }
    print('msg: {}'.format(msg))
    socketio.emit('device_output', _msg, callback=messageReceived)
    msg = bytearray.fromhex(msg)
    mqtt.publish(topic, msg)


@socketio.on('publish_event')
def handle_publish_event(data):
    print(f'handle_publish_event:: data: {data}')
    topic = data["topic"]
    msg = data['msg']
    is_hex = data['is_hex']
    address = data['address']
    power_status = data['power_status']
    recharge = data['recharge']
    prepaid = data['prepaid']
    postpaid = data['postpaid']
    prepaid_balance = data['prepaid_balance']
    postpaid_balance = data['postpaid_balance']
    c_balance = data['c_balance']
    config = data['config']
    try:
        pass
    except Exception as ex:
        msg = 'Invalid hex value: {}'.format(ex)
    publish_to_web(msg, topic)


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('#')


def process_message(msg):
    topic = msg['topic']
    data = msg['message']
    print(f'process_callback:: topic: {topic} data: {data}')
    if topic == PUB_TOPIC_CONFIG:
        payload = {
            "address": None,
            "operation": "LOGIN",
            "data": {"imei": data},
            "device_type": "DEVICE_TYPE"
        }
    elif topic == PUB_TOPIC_RELAY:
        payload = {
            "address": None,
            "operation": "PING",
            "data": {"ping": json.loads(data)},
            "device_type": "DEVICE_TYPE"
        }
    elif topic == PUB_TOPIC_UPDATE:
        payload = {
            "address": None,
            "operation": "PING",
            "data": {"ping": json.loads(data)},
            "device_type": "DEVICE_TYPE"
        }
    elif topic == PUB_TOPIC_STATUS:
        payload = {
            "address": None,
            "operation": "PING",
            "data": {"ping": json.loads(data)},
            "device_type": "DEVICE_TYPE"
        }
    else:
        payload = None


@mqtt.on_topic('home_auto/#')
def handle_messages(client, userdata, message):
    msg = {'timestamp': str(datetime.datetime.now()), 'topic': message.topic, 'message': message.payload.decode(),
           'color': '#000000'}
    msg['message'] = json.dumps(msg)
    process_message(msg)
    socketio.emit('device_output', msg, callback=messageReceived)


@mqtt.on_topic('#')
def handle_messages_all(client, userdata, message):
    msg = {'timestamp': str(datetime.datetime.now()), 'topic': message.topic, 'message': message.payload.decode()}
    print(f'handle_messages_all:: msg : {msg}')


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    print(
        f'handle_mqtt_message:: client:{client}, userdata: {userdata}, message: {message}, message.payload: {message.payload}')
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    socketio.emit('mqtt_message', data=data)


@mqtt.on_log()
def handle_logging(client, userdata, level, buf):
    print(level, buf)


if __name__ == '__main__':
    print('testing on two three')
    socketio.run(app, host='0.0.0.0', port=5000, use_reloader=False, debug=True)
