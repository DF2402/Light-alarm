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

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # 允許跨域請求

wake_up_time_str = None  
timer = None
connected_clients = set()
last_message = None
light_alarm_level = 0

# 消息隊列：用於從 Flask 線程發送消息到 WebSocket 線程
message_queue = Queue()


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

@app.route('/api/get-last-message', methods=['GET'])
def get_last_message():
    global last_message
    return jsonify({'message': last_message})

@app.route('/api/set-light-alarm-level', methods=['POST'])
def set_light_alarm_level():
    global light_alarm_level
    data = request.get_json()
    light_alarm_level = data.get('level')
    
    # 將消息放入隊列，由 WebSocket 線程處理
    message_queue.put({
        'type': 'light_level',
        'value': light_alarm_level
    })
    
    print(f"Light alarm level set to: {light_alarm_level}")
    return jsonify({'status': 'success', 'message': 'Light alarm level set successfully', 'level': light_alarm_level})

@app.route('/api/send-message', methods=['POST'])
def send_message_to_esp():
    """通用的發送消息到 ESP8266 的端點"""
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({'status': 'error', 'message': 'No message provided'}), 400
    
    # 將消息放入隊列
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
        print("❌ 無法打開攝像頭")
        return
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ 無法讀取影像")
        return
    
    # 提取特徵並判斷
    feature = extract_hog_feature(frame)
    # 這裡需要實現判斷邏輯
    # TODO: 可以通過 WebSocket 發送通知給連接的客戶端
    print("⏰ 起床時間到了！")



# websocket server for ESP8266
async def websocket_handler(websocket):
    global last_message
    print(f"ESP8266 connected: {websocket.remote_address}")
    connected_clients.add(websocket)
    
    async def send_messages():
        """處理發送消息（從隊列讀取）"""
        while True:
            try:
                # 非阻塞檢查隊列
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
                        print(f"✅ Sent to ESP8266: {message}")
                    except Exception as e:
                        print(f"❌ Failed to send: {e}")
                        # 發送失敗，重新放回隊列
                        message_queue.put(msg_data)
                        break
                
                # 短暫休眠避免忙等待
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Send task error: {e}")
                break
    
    async def receive_messages():
        """處理接收消息"""
        try:
            async for message in websocket:
                print(f"📨 Received from ESP8266: {message}")
                last_message = message
                
                # 自動回覆確認
                try:
                    reply = f"ACK:{message}"
                    await websocket.send(reply)
                    print(f"✅ Sent reply: {reply}")
                except Exception as e:
                    print(f"❌ Failed to reply: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("❌ ESP8266 已斷開連接")
        except Exception as e:
            print(f"❌ Receive error: {e}")
    
    try:
        # 同時運行發送和接收任務
        await asyncio.gather(
            send_messages(),
            receive_messages()
        )
    except Exception as e:
        print(f"❌ WebSocket handler error: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"Cleaned up connection from {websocket.remote_address}")

async def start_websocket_server():
    async with websockets.serve(websocket_handler, "0.0.0.0", 5501):
        print("WebSocket server for ESP8266: ws://0.0.0.0:5501")
        await asyncio.Future()  # 永久運行

def run_websocket_server():
    asyncio.run(start_websocket_server())

if __name__ == '__main__':
    print("start server...")
    
    ws_thread = Thread(target=run_websocket_server, daemon=True)
    ws_thread.start()
    
    print("HTTP API: http://0.0.0.0:5000")
    print("WebSocket server for ESP8266: ws://0.0.0.0:5501")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    