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
from queue import Queue
from classifier import Classifier

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

wake_up_time_str = None  
timer = None
connected_clients = set()
last_message = None
light_alarm_level = 0

message_queue = Queue()

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
    global light_alarm_level
    data = request.get_json()
    light_alarm_level = data.get('level')
    
    message_queue.put({
        'type': 'light_level',
        'value': light_alarm_level
    })
    
    print(f"Light alarm level set to: {light_alarm_level}")
    return jsonify({'status': 'success', 'message': 'Light alarm level set successfully', 'level': light_alarm_level})

@app.route('/api/send-message', methods=['POST'])
def send_message_to_esp():

    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({'status': 'error', 'message': 'No message provided'}), 400
    
    message_queue.put({
        'type': 'custom',
        'message': message
    })
    
    print(f"Queued message to ESP8266: {message}")
    return jsonify({'status': 'success', 'message': 'Message queued for sending'})
     
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



# websocket server for IOT device
async def websocket_handler(websocket):
    global last_message
    print(f"Device connected: {websocket.remote_address}")
    connected_clients.add(websocket)
    
    async def send_messages():
        while True:
            try:
                if not message_queue.empty():
                    msg_data = message_queue.get_nowait()
                    
                    if msg_data['type'] == 'light_level':
                        message = f"light_alarm_level:{msg_data['value']}"
                    elif msg_data['type'] == 'custom':
                        message = msg_data['message']
                    else:
                        message = str(msg_data)
                    
                    try:
                        await websocket.send(message)
                        print(f"Sent to ESP8266: {message}")
                    except Exception as e:
                        print(f"Failed to send: {e}")
                        message_queue.put(msg_data)
                        break
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Send task error: {e}")
                break
    
    async def receive_messages():
        try:
            async for message in websocket:
                print(f"Received from ESP8266: {message}")
                last_message = message
                
                try:
                    reply = f"ACK:{message}"
                    await websocket.send(reply)
                    print(f"Sent reply: {reply}")
                except Exception as e:
                    print(f"Failed to reply: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("ESP8266 disconnected")
        except Exception as e:
            print(f"Receive error: {e}")
    
    try:
        await asyncio.gather(
            send_messages(),
            receive_messages()
        )
    except Exception as e:
        print(f"WebSocket handler error: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"Cleaned up connection from {websocket.remote_address}")

async def start_websocket_server():
    async with websockets.serve(websocket_handler, "0.0.0.0", 5501):
        print("WebSocket server for ESP8266: ws://0.0.0.0:5501")
        await asyncio.Future()

def run_websocket_server():
    asyncio.run(start_websocket_server())

if __name__ == '__main__':
    print("start server...")
    
    ws_thread = Thread(target=run_websocket_server, daemon=True)
    ws_thread.start()
    
    print("HTTP API: http://0.0.0.0:5502")
    print("WebSocket server for ESP8266: ws://0.0.0.0:5501")
    
    app.run(host='0.0.0.0', port=5502, debug=True, use_reloader=False)
    