from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from threading import Timer
import datetime
import cv2
import json
import base64
import numpy as np
from train import extract_hog_feature 

app = Flask(__name__)
CORS(app)  # 允許跨域請求

wake_up_time_str = None  
timer = None

with open('features.json', 'r') as f:
    data = json.load(f)
    person_features = np.array(data['on_bed'])
    no_person_features = np.array(data['off_bed'])

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
    if not cap.isOpened():
        return jsonify({'status': 'error', 'message': 'Failed to open camera'})
    ret, frame = cap.read()
    if not ret:
        return jsonify({'status': 'error', 'message': 'Failed to capture image'})
    success, buffer = cv2.imencode('.jpg', frame)
    if not success:
        return jsonify({'status': 'error', 'message': 'Failed to encode image'})
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    cap.release()
    return jsonify({'status': 'success', 'message': 'Image captured successfully', 'image': image_base64})

def set_wake_time(time_str):
    global wake_up_time_str, timer
    wake_up_time_str = time_str

    if timer:
        timer.cancel()

    now = datetime.datetime.now()
    target_time = datetime.datetime.strptime(time_str, '%H:%M').replace(
        year=now.year, month=now.month, day=now.day)
    if target_time <= now:
        target_time += datetime.timedelta(days=1)  # 跨天

    seconds_until = (target_time - now).total_seconds()

    timer = Timer(seconds_until, check_bed_presence)
    timer.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)