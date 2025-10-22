import numpy as np
from PIL import Image
import os

def load_images_from_folder(folder):
    images = []
    for filename in os.listdir(folder):
        if filename.endswith('.png') or filename.endswith('.jpg'):
            img_path = os.path.join(folder, filename)
            img = Image.open(img_path).convert('L')  
            images.append(np.array(img))
    return images

sobel_x = np.array([[ -1, 0, 1],
                    [ -2, 0, 2],
                    [ -1, 0, 1]])

sobel_y = np.array([[ -1, -2, -1],
                    [  0,  0,  0],
                    [  1,  2,  1]])

def convolve2d(image, kernel):
    k_height, k_width = kernel.shape
    pad_h = k_height // 2
    pad_w = k_width // 2
    padded_img = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), mode='constant', constant_values=0)
    output = np.zeros_like(image, dtype=float)
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            region = padded_img[i:i+k_height, j:j+k_width]
            output[i, j] = np.sum(region * kernel)
    return output

def compute_gradients(image):
    gx = convolve2d(image, sobel_x)
    gy = convolve2d(image, sobel_y)
    magnitude = np.sqrt(gx**2 + gy**2)
    angle = np.arctan2(gy, gx) * (180 / np.pi)
    angle[angle < 0] += 180  
    return magnitude, angle

def extract_hog_feature(image, cell_size=8, bins=9):
    mag, angle = compute_gradients(image)
    h, w = mag.shape
    cell_x = w 
    cell_y = h 
    hog = []

    for i in range(cell_y):
        for j in range(cell_x):
            mag_cell = mag[i*cell_size:(i+1)*cell_size, j*cell_size:(j+1)*cell_size]
            angle_cell = angle[i*cell_size:(i+1)*cell_size, j*cell_size:(j+1)*cell_size]
            hist = np.zeros(bins)
            for m in range(mag_cell.shape[0]):
                for n in range(mag_cell.shape[1]):
                    mag_value = mag_cell[m, n]
                    angle_value = angle_cell[m, n]
                    bin_idx = int(angle_value // (180 / bins))
                    hist[bin_idx % bins] += mag_value
            hog.extend(hist)
    return np.array(hog)

if __name__ == "__main__":
    on_bed_dataset = ""
    off_bed_dataset = ""

    on_bed = load_images_from_folder(on_bed_dataset)
    off_bed = load_images_from_folder(off_bed_dataset)

    on_bed_features =[extract_hog_feature(img) for img in on_bed]
    off_bed_features = [extract_hog_feature(img) for img in off_bed]

    on_bed_features_list = [feat.tolist() for feat in on_bed_features]
    off_bed_features_list = [feat.tolist() for feat in off_bed_features]
    
    features_data = {
        'on_bed': on_bed_features_list,
        'off_bed': off_bed_features_list
    }

    with open('features.json', 'w') as f:
        json.dump(features_list, f)