import cv2
import numpy as np
import os
import joblib
from classifier import Classifier
from train import extract_hog_feature
from sklearn import svm
from datetime import datetime

# load model
classifier = Classifier()

# 實時 feedback training 資料儲存
feedback_data = {
    'features': [],
    'labels': [],
    'images': []
}

# 建立 feedback 資料夾
feedback_dir = './feedback_data'
os.makedirs(feedback_dir, exist_ok=True)
os.makedirs(os.path.join(feedback_dir, 'on-bed'), exist_ok=True)
os.makedirs(os.path.join(feedback_dir, 'off-bed'), exist_ok=True)

# open camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("無法開啟攝影機,嘗試使用其他索引...")
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("仍然無法開啟攝影機")
        exit()

# 設定攝影機屬性
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# 等待攝影機初始化
import time
time.sleep(2)

print("=" * 60)
print("攝影機已開啟 - 實時 Feedback Training 模式")
print("=" * 60)
print("操作說明:")
print("  q: 退出程式")
print("  1: 標記當前畫面為 'on-bed' (床上有人)")
print("  0: 標記當前畫面為 'off-bed' (床上無人)")
print("  r: 使用收集的 feedback 資料重新訓練模型")
print("  s: 顯示當前收集的 feedback 資料統計")
print("=" * 60)

def add_feedback(frame, label_str):
    """添加 feedback 資料"""
    # 轉換為灰度並提取特徵
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (128, 128))
    feature = extract_hog_feature(resized)
    
    # 儲存特徵和標籤
    feedback_data['features'].append(feature)
    feedback_data['labels'].append(1 if label_str == 'on-bed' else 0)
    feedback_data['images'].append(frame.copy())
    
    # 儲存圖片到對應資料夾
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{timestamp}.jpg"
    filepath = os.path.join(feedback_dir, label_str, filename)
    cv2.imwrite(filepath, frame)
    
    print(f"✓ 已標記為 '{label_str}' (共收集 {len(feedback_data['labels'])} 筆資料)")
    return True

def retrain_model():
    """使用 feedback 資料重新訓練模型"""
    if len(feedback_data['labels']) < 2:
        print("✗ 資料不足，至少需要 2 筆 feedback 資料才能重新訓練")
        return False
    
    print("\n" + "=" * 60)
    print("開始重新訓練模型...")
    print("=" * 60)
    
    # 載入原始訓練資料
    try:
        original_model = joblib.load('svm_model.pkl')
        print("✓ 已載入原始模型")
    except:
        print("✗ 無法載入原始模型")
        return False
    
    # 合併 feedback 資料
    X_feedback = np.array(feedback_data['features'])
    y_feedback = np.array(feedback_data['labels'])
    
    print(f"✓ Feedback 資料: {len(y_feedback)} 筆")
    print(f"  - on-bed: {np.sum(y_feedback == 1)} 筆")
    print(f"  - off-bed: {np.sum(y_feedback == 0)} 筆")
    
    # 使用 feedback 資料進行增量訓練
    # 注意: 這裡我們重新訓練整個模型，因為 sklearn 的 SVM 不支援真正的增量學習
    # 實際應用中，你可能需要保存原始訓練資料並與 feedback 資料合併
    
    new_model = svm.SVC(kernel='rbf', C=1.0, gamma='scale')
    new_model.fit(X_feedback, y_feedback)
    
    # 儲存新模型
    backup_path = f'svm_model_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
    joblib.dump(classifier.svm, backup_path)
    print(f"✓ 原始模型已備份至: {backup_path}")
    
    joblib.dump(new_model, 'svm_model.pkl')
    print("✓ 新模型已儲存至: svm_model.pkl")
    
    # 重新載入模型到 classifier
    classifier.svm = new_model
    print("✓ 模型已更新")
    
    print("=" * 60)
    print("重新訓練完成！")
    print("=" * 60 + "\n")
    
    return True

def show_stats():
    """顯示 feedback 資料統計"""
    total = len(feedback_data['labels'])
    if total == 0:
        print("\n目前尚未收集任何 feedback 資料\n")
        return
    
    on_bed_count = sum(1 for label in feedback_data['labels'] if label == 1)
    off_bed_count = total - on_bed_count
    
    print("\n" + "=" * 60)
    print("Feedback 資料統計")
    print("=" * 60)
    print(f"總計: {total} 筆")
    print(f"  - on-bed (床上有人): {on_bed_count} 筆 ({on_bed_count/total*100:.1f}%)")
    print(f"  - off-bed (床上無人): {off_bed_count} 筆 ({off_bed_count/total*100:.1f}%)")
    print("=" * 60 + "\n")

frame_count = 0
current_frame = None

while True:
    ret, frame = cap.read()
    if not ret:
        frame_count += 1
        if frame_count > 5:
            print("連續無法讀取影像,退出程式")
            break
        print(f"無法讀取影像 (嘗試 {frame_count}/5)")
        time.sleep(0.5)
        continue
    
    frame_count = 0  # 重置計數器
    current_frame = frame.copy()
    
    # predict
    result = classifier.classify(frame)
    
    if result == 'on-bed':
        label = 'on-bed'
        color = (0, 255, 0)  # green
    else:
        label = 'off-bed'
        color = (0, 0, 255)  # red
    
    # display result on frame
    cv2.putText(frame, f"Prediction: {label}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    
    # 顯示 feedback 資料統計
    feedback_count = len(feedback_data['labels'])
    cv2.putText(frame, f"Feedback: {feedback_count} samples", (10, 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # 顯示操作提示
    cv2.putText(frame, "Press: 1=on-bed | 0=off-bed | r=retrain | s=stats | q=quit", 
                (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # show frame
    cv2.imshow('Bed Detection - Feedback Training Mode', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    elif key == ord('1'):
        # 標記為 on-bed
        add_feedback(current_frame, 'on-bed')
    elif key == ord('0'):
        # 標記為 off-bed
        add_feedback(current_frame, 'off-bed')
    elif key == ord('r'):
        # 重新訓練模型
        retrain_model()
    elif key == ord('s'):
        # 顯示統計
        show_stats()

cap.release()
cv2.destroyAllWindows()

# 程式結束時顯示最終統計
print("\n程式結束")
show_stats()