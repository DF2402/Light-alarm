from flask import Flask, render_template, request, jsonify
from threading import Timer
import datetime
form train import extract_hog_feature 
app = Flask(__name__)

wake_up_time_str = None  
timer = None

with open('features.json', 'r') as f:
    data = json.load(f)
    person_features = np.array(data['person'])
    no_person_features = np.array(data['no_person'])
@app.route('/api/timer-time', methods=['GET'])
def get_time():
    global wake_up_time_str
    return jsonify({'time': wake_up_time_str})

@app.route('/api/set-timer', methods=['POST'])
def set_time():
    global wake_up_time_str
    data = request.get_json()
    wake_up_time_str = data.get('time')
    set_wake_time(wake_up_time_str)
    return jsonify({"status": "success"})

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


def chi_square_distance(histA, histB):
    eps = 1e-10
    return 0.5 * np.sum(((histA - histB) ** 2) / (histA + histB + eps))

def check_bed_presence():
    print(f"checking (time:{wake_up_time_str})")
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("fail to open camera")
        return
    current_feature = extract_hog_feature(frame)
    dist_person = np.min([chi_square_distance(current_feature, feat) for feat in person_features])
    dist_no_person = np.min([chi_square_distance(current_feature, feat) for feat in no_person_features])

    threshold = 0.5

    if dist_person < threshold:
        print("find person")
    elif dist_no_person < threshold:
        print("no person ")
    else:
        print("fail to detect")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)