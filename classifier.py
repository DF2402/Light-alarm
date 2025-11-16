import cv2
import numpy as np
import os
import joblib

class Classifier:
    def __init__(self):
        try:
            self.svm = joblib.load('svm_model.pkl')
        except Exception as e:
            print(f"Error loading model: {e} model not found")
            self.svm = None

    def classify(self, image):
        # convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # resize to 128x128
        resized = cv2.resize(gray, (128, 128))
        # canny edge detection
        edges = cv2.Canny(resized, 100, 200)
        # hog descriptor
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        features = hog.compute(edges).flatten().reshape(1, -1)
        result = self.svm.predict(features)[0]
        if result == 1:
            return 'on-bed'
        else:
            return 'off-bed'
            
