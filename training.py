import cv2
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report
import matplotlib.pyplot as plt
import joblib

on_bed_dataset = "./3127_dataset/on-bed"
off_bed_dataset = "./3127_dataset/off-bed"

on_bed_images = [cv2.imread(os.path.join(on_bed_dataset, img)) for img in os.listdir(on_bed_dataset) if img.endswith(('.jpg', '.png'))]
off_bed_images = [cv2.imread(os.path.join(off_bed_dataset, img)) for img in os.listdir(off_bed_dataset) if img.endswith(('.jpg', '.png'))]

# turn in to grayscale
on_bed_images = [cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) for img in on_bed_images]
off_bed_images = [cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) for img in off_bed_images]

# resize to 128x128
on_bed_images = [cv2.resize(img, (128, 128)) for img in on_bed_images]
off_bed_images = [cv2.resize(img, (128, 128)) for img in off_bed_images]

# canny edge detection
on_bed_images = [cv2.Canny(img, 100, 200) for img in on_bed_images]
off_bed_images = [cv2.Canny(img, 100, 200) for img in off_bed_images]

# hog descriptor
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
on_bed_features = [hog.compute(img).flatten() for img in on_bed_images]
off_bed_features = [hog.compute(img).flatten() for img in off_bed_images]

# combine all data
X = np.vstack([on_bed_features, off_bed_features])
y = np.hstack([np.ones(len(on_bed_features)), np.zeros(len(off_bed_features))])

# split into train and test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# train SVM classifier
print("訓練 SVM 分類器中...")
svm = SVC(kernel='linear')
svm.fit(X_train, y_train)

# test classifier
print("測試分類器中...")
y_pred = svm.predict(X_test)

# calculate accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"\n準確率: {accuracy:.2%}")
print("\n分類報告:")
print(classification_report(y_test, y_pred, target_names=['off-bed', 'on-bed']))

# save model
joblib.dump(svm, 'svm_model.pkl')