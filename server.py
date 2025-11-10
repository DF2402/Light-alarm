from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from threading import Timer, Thread
import datetime
import cv2
import json
import base64
import numpy as np
from train import extract_hog_feature 
import asyncio
import websockets
from classifier import Classifier
from websocket_server import WebsocketServer

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

wake_up_time_str = None  
timer = None
connected_clients = set()
last_message = None
light_alarm_level = 0
ws_server = None  # 全域 WebSocket 伺服器實例

@app.route('/api/timer-time', methods=['GET'])
def get_timer_time():
    global wake_up_time_str
    if wake_up_time_str is None:
        return jsonify({'timer_time': "No timer set"})
    return jsonify({'timer_time': wake_up_time_str})

@app.route('/api/set-timer', methods=['POST'])
def set_time():
    global wake_up_time_str
    data = request.get_json()
    wake_up_time_str = data.get('time')
    set_wake_time(wake_up_time_str)
    return jsonify({"status": "success"})

@app.route('/api/take-image', methods=['GET'])
def capture_image():
    cap = cv2.VideoCapture(0)
    classifier = Classifier()
    if not cap.isOpened():
        return jsonify({'status': 'error', 'message': 'Failed to open camera'})
    ret, frame = cap.read()
    success, buffer = cv2.imencode('.jpg', frame)
    if not success:
        return jsonify({'status': 'error', 'message': 'Failed to encode image'})
    image = base64.b64encode(buffer).decode('utf-8')
    result = classifier.classify(frame)
    print(f"Result: {result}")
    cap.release()
    return jsonify({'status': 'success', 'message': 'Image captured successfully', 'image': image, 'result': result})

@app.route('/api/get-last-message', methods=['GET'])
def get_last_message():
    global last_message
    return jsonify({'message': last_message})

@app.route('/api/set-light-alarm-level', methods=['POST'])
def set_light_alarm_level():
    global light_alarm_level, ws_server
    data = request.get_json()
    light_alarm_level = data.get('level')
    
    # 直接透過 WebSocket 伺服器發送
    if ws_server:
        ws_server.send_to_client(f"LIGHT:{light_alarm_level}")
    
    print(f"Light alarm level set to: {light_alarm_level}")
    return jsonify({'status': 'success', 'message': 'Light alarm level set successfully', 'level': light_alarm_level})

@app.route('/api/send-message', methods=['POST'])
def send_message_to_esp():
    global ws_server
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({'status': 'error', 'message': 'No message provided'}), 400
    
    # 直接透過 WebSocket 伺服器發送
    if ws_server:
        success = ws_server.send_to_client(message)
        if success:
            print(f"Sent message to ESP8266: {message}")
            return jsonify({'status': 'success', 'message': 'Message sent'})
        else:
            return jsonify({'status': 'error', 'message': 'No client connected'}), 503
    
    return jsonify({'status': 'error', 'message': 'WebSocket server not ready'}), 503
     
def set_wake_time(time_str):
    global wake_up_time_str, timer
    wake_up_time_str = time_str

    if timer:
        timer.cancel()

    now = datetime.datetime.now()
    target_time = datetime.datetime.strptime(time_str, '%H:%M').replace(
        year=now.year, month=now.month, day=now.day)
    if target_time <= now:
        target_time += datetime.timedelta(days=1)  

    seconds_until = (target_time - now).total_seconds()

    timer = Timer(seconds_until, check_bed_presence)
    timer.start()


def check_bed_presence():
    """檢查床上是否有人的函數"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Failed to open camera")
        return
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("Failed to read image")
        return False

    result = Classifier().classify(frame)
    if result == 'on-bed':
        return True 
    else:
        return False

if __name__ == '__main__':
    print("start server...")
    
    # 啟動 WebSocket 伺服器
    ws_server = WebsocketServer()
    ws_server.start_in_thread()
    
    print("HTTP API: http://0.0.0.0:5502")
    print("WebSocket server for ESP8266: ws://0.0.0.0:5501")
    
    app.run(host='0.0.0.0', port=5502, debug=True, use_reloader=False)
    