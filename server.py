from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from threading import Timer
import datetime
import cv2
import base64
import time
from classifier import Classifier
from websocket_server import WebsocketServer
from sensor_db import SensorDB

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

sensor_db = SensorDB('sensor_data.db')

wake_up_time_str = None  
timer = None
ws_server = None

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

@app.route('/api/devices', methods=['GET'])
def get_device_list():
    global ws_server
    if ws_server:
        device_list = ws_server.get_device_list()
        print(f"Device list: {device_list}")
        return jsonify({
            'status': 'success',
            'devices': device_list
        })
    return jsonify({
        'status': 'error',
        'message': 'Failed to get device list'
    }), 500


@app.route('/api/send_toggle/<device_id>', methods=['GET'])
def send_led_command(device_id, value='toggle'):
    global ws_server
    if ws_server:
        try:
            ws_server.send_led_command(device_id, value)
            return jsonify({
                'status': 'success',
                'message': f'Message sent to {device_id}: {value}'
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Error sending toggle command: {e}'
            }), 500
    else:
        return jsonify({
            'status': 'error',
            'message': 'WebSocket server not running'
        }), 500

@app.route('/api/sensor-data/<device_id>', methods=['GET'])
def get_sensor_data( device_id ):
    global ws_server
    if ws_server:
        sensor_data = ws_server.get_sensor_data(device_id)
        if sensor_data:
            return jsonify({
                'status': 'success',
                'sensor_data': sensor_data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to get sensor data for device {device_id}'
            }), 500
    return jsonify({
        'status': 'error',
        'message': f'Failed to get sensor data for device {device_id}'
    }), 500


@app.route('/api/sensor-history/<device_id>', methods=['GET'])
def get_sensor_history_hourly(device_id):
    sensor_id = request.args.get('sensor_id')
    hours = request.args.get('hours', 24, type=int)
    
    try:
        data = sensor_db.get_hourly_average(device_id, sensor_id, hours)
        
        simplified_data = [
            {'timestamp': item['timestamp'], 'value': item['value']}
            for item in data
        ]
        
        return jsonify({
            'status': 'success',
            'device_id': device_id,
            'count': len(simplified_data),
            'data': simplified_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500

@app.route('/api/last-detection', methods=['GET'])
def get_last_detection():
    try:
        record = sensor_db.get_latest_detection()
        if record:
            return jsonify({
                'status': 'success',
                'image': record['image_data'],
                'detection_result': record['result'],
                'detection_time': record['timestamp']
            })
        else:
            return jsonify({
                'status': 'failed',
                'message': 'No detection record available'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500

@app.route('/api/detection-history', methods=['GET'])
def get_detection_history():
    limit = request.args.get('limit', 10, type=int)
    
    try:
        records = sensor_db.get_detection_history(limit)
        return jsonify({
            'status': 'success',
            'count': len(records),
            'data': records
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500

def save_sensor_data_to_db(device_id, sensor_id, value):
    success = sensor_db.insert_sensor_data(device_id, sensor_id, value)
    if success:
        print(f"[Server] Saved: {device_id} - {sensor_id}: {value}")
    else:
        print(f"[Server] Failed: {device_id} - {sensor_id}: {value}")

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
    ws_server.send_led_command('alarm-clock', 'on')
    time.sleep(1)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Server] Failed to open camera")
        return False
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("[Server] Failed to read image")
        return False

    result = Classifier().classify(frame)
    
    _, buffer = cv2.imencode(".jpg", frame)
    image_base64 = base64.b64encode(buffer).decode("utf-8")
    
    sensor_db.save_detection(image_base64, result)
    print(f"[Server] Detection saved: {result}")
    
    if result == 'on-bed':
        return True
    else:
        ws_server.send_led_command('alarm-clock', 'off')
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("Smart Light Alarm Server")
    print("=" * 50)
    
    ws_server = WebsocketServer(on_sensor_data=save_sensor_data_to_db)
    ws_server.start_in_thread()
    
    print("\nServer is running:")
    print("  HTTP API: http://0.0.0.0:5502")
    print("  WebSocket: ws://0.0.0.0:5501")
    print("=" * 50 + "\n")
    
    app.run(host='0.0.0.0', port=5502, debug=True, use_reloader=False)
    