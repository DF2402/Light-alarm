import cv2
import numpy as np
import os
import joblib

# load model
svm = joblib.load('svm_model.pkl')

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

print("攝影機已開啟,按 'q' 退出")

frame_count = 0
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
    
    # convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # resize to 128x128 (same as training)
    resized = cv2.resize(gray, (128, 128))
    
    # canny edge detection
    edges = cv2.Canny(resized, 100, 200)
    
    # hog descriptor
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    features = hog.compute(edges).flatten().reshape(1, -1)
    
    # predict
    result = svm.predict(features)[0]
    
    if result == 1:
        label = 'on-bed'
        color = (0, 255, 0)  # green
    else:
        label = 'off-bed'
        color = (0, 0, 255)  # red
    
    # display result on frame
    cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    
    # show frame
    cv2.imshow('Bed Detection', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()