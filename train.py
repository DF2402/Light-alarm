import numpy as np
from PIL import Image
import os
import json
from scipy import signal
from tqdm import tqdm

def load_images_from_folder(folder, target_size=(128, 128)):
    """
    從資料夾載入圖像並調整大小
    
    Args:
        folder: 圖像資料夾路徑
        target_size: 目標圖像大小 (width, height)
    
    Returns:
        圖像列表
    """
    images = []
    filenames = []
    
    if not os.path.exists(folder):
        print(f"警告: 資料夾不存在 - {folder}")
        return images, filenames
    
    image_files = [f for f in os.listdir(folder) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    print(f"從 {folder} 載入 {len(image_files)} 個圖像...")
    
    for filename in tqdm(image_files, desc=f"載入圖像"):
        try:
            img_path = os.path.join(folder, filename)
            img = Image.open(img_path).convert('L')
            # 調整圖像大小以減少內存使用和加快處理速度
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            images.append(np.array(img))
            filenames.append(filename)
        except Exception as e:
            print(f"\n錯誤: 無法載入 {filename}: {e}")
    
    return images, filenames

sobel_x = np.array([[ -1, 0, 1],
                    [ -2, 0, 2],
                    [ -1, 0, 1]])

sobel_y = np.array([[ -1, -2, -1],
                    [  0,  0,  0],
                    [  1,  2,  1]])

def convolve2d(image, kernel):
    """
    使用 scipy 的優化卷積函數，比純 Python 循環快得多
    """
    return signal.convolve2d(image, kernel, mode='same', boundary='fill', fillvalue=0)

def compute_gradients(image):
    gx = convolve2d(image, sobel_x)
    gy = convolve2d(image, sobel_y)
    magnitude = np.sqrt(gx**2 + gy**2)
    angle = np.arctan2(gy, gx) * (180 / np.pi)
    angle[angle < 0] += 180  
    return magnitude, angle

def extract_hog_feature(image, cell_size=8, bins=9):
    """
    提取 HOG (Histogram of Oriented Gradients) 特徵
    
    Args:
        image: 輸入的灰度圖像
        cell_size: 單元格大小
        bins: 方向直方圖的箱數
    
    Returns:
        HOG 特徵向量
    """
    mag, angle = compute_gradients(image)
    h, w = mag.shape
    
    # 修正：計算單元格數量
    cell_y = h // cell_size
    cell_x = w // cell_size
    
    hog = []

    for i in range(cell_y):
        for j in range(cell_x):
            mag_cell = mag[i*cell_size:(i+1)*cell_size, j*cell_size:(j+1)*cell_size]
            angle_cell = angle[i*cell_size:(i+1)*cell_size, j*cell_size:(j+1)*cell_size]
            
            # 優化：使用向量化操作而不是嵌套循環
            hist = np.zeros(bins)
            bin_indices = (angle_cell // (180 / bins)).astype(int) % bins
            
            for bin_idx in range(bins):
                mask = bin_indices == bin_idx
                hist[bin_idx] = np.sum(mag_cell[mask])
            
            hog.extend(hist)
    
    return np.array(hog)

if __name__ == "__main__":
    print("=" * 60)
    print("HOG 特徵提取程序")
    print("=" * 60)
    
    # 定義數據集路徑
    on_bed_dataset = "./3127 dataset/bed"
    off_bed_dataset = "./3127 dataset/non-bed"
    
    # 圖像大小設定（可調整以平衡速度和精度）
    IMAGE_SIZE = (128, 128)  # 較小的尺寸以減少內存使用
    
    # 載入圖像
    print("\n步驟 1: 載入圖像...")
    on_bed, on_bed_files = load_images_from_folder(on_bed_dataset, target_size=IMAGE_SIZE)
    off_bed, off_bed_files = load_images_from_folder(off_bed_dataset, target_size=IMAGE_SIZE)
    
    if len(on_bed) == 0:
        print(f"\n警告: 在 {on_bed_dataset} 中沒有找到圖像")
        print("請確保資料夾存在並包含圖像文件")
    
    if len(off_bed) == 0:
        print(f"\n警告: 在 {off_bed_dataset} 中沒有找到圖像")
        print("請確保資料夾存在並包含圖像文件")
    
    if len(on_bed) == 0 and len(off_bed) == 0:
        print("\n錯誤: 沒有找到任何圖像，程序退出")
        exit(1)
    
    # 提取 HOG 特徵
    print(f"\n步驟 2: 提取 HOG 特徵...")
    print(f"在床圖像: {len(on_bed)} 張")
    print(f"不在床圖像: {len(off_bed)} 張")
    
    on_bed_features = []
    if len(on_bed) > 0:
        print("\n處理在床圖像...")
        for img in tqdm(on_bed, desc="提取在床特徵"):
            on_bed_features.append(extract_hog_feature(img))
    
    off_bed_features = []
    if len(off_bed) > 0:
        print("\n處理不在床圖像...")
        for img in tqdm(off_bed, desc="提取不在床特徵"):
            off_bed_features.append(extract_hog_feature(img))
    
    # 轉換為列表格式以便 JSON 序列化
    print("\n步驟 3: 準備保存數據...")
    on_bed_features_list = [feat.tolist() for feat in on_bed_features]
    off_bed_features_list = [feat.tolist() for feat in off_bed_features]
    
    features_data = {
        'on_bed': on_bed_features_list,
        'off_bed': off_bed_features_list,
        'on_bed_files': on_bed_files,
        'off_bed_files': off_bed_files,
        'image_size': IMAGE_SIZE,
        'feature_length': len(on_bed_features_list[0]) if on_bed_features_list else 0
    }
    
    # 保存特徵到 JSON 文件
    output_file = 'features.json'
    print(f"\n步驟 4: 保存特徵到 {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(features_data, f, indent=2)
    
    print("\n" + "=" * 60)
    print("完成!")
    print("=" * 60)
    print(f"總共處理: {len(on_bed) + len(off_bed)} 張圖像")
    print(f"特徵維度: {features_data['feature_length']}")
    print(f"輸出文件: {output_file}")
    print("=" * 60)