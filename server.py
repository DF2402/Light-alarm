from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from threading import Timer
import datetime
import cv2
import base64
from classifier import Classifier
from websocket_server import WebsocketServer
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

engine = create_engine('sqlite:///sensor_data.db', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class SensorData(Base):
    __tablename__ = 'sensor_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(50), nullable=False, index=True)
    sensor_id = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'sensor_id': self.sensor_id,
            'value': self.value,
            'timestamp': self.timestamp.isoformat()
        }

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
def send_led_command(device_id):
    global ws_server
    if ws_server:
        try:
            ws_server.send_led_command(device_id, 'toggle')
            return jsonify({
                'status': 'success',
                'message': f'Message sent to {device_id}: toggle'
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
def get_sensor_history(device_id):
    sensor_id = request.args.get('sensor_id')
    limit = request.args.get('limit', 100, type=int)
    hours = request.args.get('hours', type=int)
    
    session = Session()
    try:
        query = session.query(SensorData).filter(SensorData.device_id == device_id)
        
        if sensor_id:
            query = query.filter(SensorData.sensor_id == sensor_id)
        
        if hours:
            time_threshold = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
            query = query.filter(SensorData.timestamp >= time_threshold)
        
        results = query.order_by(SensorData.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'status': 'success',
            'device_id': device_id,
            'count': len(results),
            'data': [record.to_dict() for record in results]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500
    finally:
        session.close()

def save_sensor_data_to_db(device_id, sensor_id, value):
    session = Session()
    try:
        sensor_data = SensorData(
            device_id=device_id,
            sensor_id=sensor_id,
            value=float(value)
        )
        session.add(sensor_data)
        session.commit()
        print(f"save sensor data to db: {device_id} - {sensor_id}: {value}")
    except Exception as e:
        session.rollback()
        print(f"save sensor data to db failed: {e}")
    finally:
        session.close()

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
        send_led_command('alarm-clock', 'on')
        return True 
    else:
        send_led_command('alarm-clock', 'off')
        return False

if __name__ == '__main__':
    print("start server...")
    
    print("initialize database...")
    Base.metadata.create_all(engine)
    print("database initialized")
    
    ws_server = WebsocketServer(on_sensor_data=save_sensor_data_to_db)
    ws_server.start_in_thread()
    
    print("HTTP API: http://0.0.0.0:5502")
    print("WebSocket: ws://0.0.0.0:5501")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5502, debug=True, use_reloader=False)
    