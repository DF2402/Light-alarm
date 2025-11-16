import cv2
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report
import matplotlib.pyplot as plt
import joblib
import random
from PIL import Image, ImageOps

on_bed_dataset = "./3127_dataset/on-bed"
off_bed_dataset = "./3127_dataset/off-bed"

on_bed_images = [cv2.imread(os.path.join(on_bed_dataset, img)) for img in os.listdir(on_bed_dataset) if img.endswith(('.jpg', '.png'))]
off_bed_images = [cv2.imread(os.path.join(off_bed_dataset, img)) for img in os.listdir(off_bed_dataset) if img.endswith(('.jpg', '.png'))]

def augment_images(np_images, image_size=(128, 128)):
    augmented = []
    w, h = image_size

    for np_img in np_images:
        img = Image.fromarray(np.uint8(np_img))

        zoom_factor = random.uniform(1.0, 1.3)  # 1.0~1.3 倍
        zw, zh = int(w * zoom_factor), int(h * zoom_factor)
        img_zoom = img.resize((zw, zh), Image.Resampling.LANCZOS)

        left = (zw - w) // 2
        top = (zh - h) // 2
        img = img_zoom.crop((left, top, left + w, top + h))

        max_shift_x = int(0.1 * w)
        max_shift_y = int(0.1 * h)
        shift_x = random.randint(-max_shift_x, max_shift_x)
        shift_y = random.randint(-max_shift_y, max_shift_y)

        shifted = Image.new("L", (w, h), 0)
        shifted.paste(img, (shift_x, shift_y))
        img = shifted

        if random.random() > 0.5:
            img = ImageOps.mirror(img)

        augmented.append(np.array(img))

    return augmented
extend_on_bed_1 = augment_images(on_bed_images)
extend_off_bed_1 = augment_images(off_bed_images)
extend_on_bed_2 = augment_images(on_bed_images)
extend_off_bed_2 = augment_images(off_bed_images)
extend_on_bed_3 = augment_images(on_bed_images)
extend_off_bed_3 = augment_images(off_bed_images)



on_bed_images += extend_on_bed_1 + extend_on_bed_2 + extend_on_bed_3
off_bed_images += extend_off_bed_1 + extend_off_bed_2 + extend_off_bed_3

# turn in to grayscale
on_bed_images = [
    cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    for img in on_bed_images
]
off_bed_images = [
    cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    for img in off_bed_images
]

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
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=30)

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