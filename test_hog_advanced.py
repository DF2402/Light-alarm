"""
HOG 特徵測試腳本 - 進階版
包含特徵歸一化、不同k值測試、交叉驗證
"""
import numpy as np
import json
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

def load_features(filename='features.json'):
    """載入特徵文件"""
    print("載入特徵文件...")
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

def prepare_dataset(features_data):
    """準備訓練和測試數據集"""
    print("\n準備數據集...")
    
    # 提取特徵和標籤
    on_bed_features = np.array(features_data['on_bed'])
    off_bed_features = np.array(features_data['off_bed'])
    
    # 創建標籤 (1 = 在床, 0 = 不在床)
    on_bed_labels = np.ones(len(on_bed_features))
    off_bed_labels = np.zeros(len(off_bed_features))
    
    # 合併數據
    X = np.vstack([on_bed_features, off_bed_features])
    y = np.hstack([on_bed_labels, off_bed_labels])
    
    print(f"總樣本數: {len(X)}")
    print(f"  在床: {len(on_bed_features)}")
    print(f"  不在床: {len(off_bed_features)}")
    print(f"特徵維度: {X.shape[1]}")
    
    return X, y, features_data

def chi_square_distance_sklearn(x, y):
    """Chi-square 距離函數（sklearn 可用）"""
    epsilon = 1e-10
    return np.sum((x - y) ** 2 / (x + y + epsilon))

def test_with_normalization(X, y, metric_name, distance_metric, normalize=True):
    """測試帶歸一化的性能"""
    
    # 分割數據集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    # 特徵歸一化
    if normalize and distance_metric != 'chi2':
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
    
    # 測試不同的 k 值
    k_values = [1, 3, 5]
    best_accuracy = 0
    best_k = 1
    best_pred = None
    
    for k in k_values:
        if distance_metric == 'chi2':
            # 使用自定義 chi-square 距離
            knn = KNeighborsClassifier(n_neighbors=k, metric=chi_square_distance_sklearn)
        else:
            knn = KNeighborsClassifier(n_neighbors=k, metric=distance_metric)
        knn.fit(X_train, y_train)
        y_pred = knn.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_k = k
            best_pred = y_pred
    
    # 使用最佳 k 值評估
    accuracy = accuracy_score(y_test, best_pred)
    precision = precision_score(y_test, best_pred, zero_division=0)
    recall = recall_score(y_test, best_pred, zero_division=0)
    f1 = f1_score(y_test, best_pred, zero_division=0)
    cm = confusion_matrix(y_test, best_pred)
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'confusion_matrix': cm,
        'best_k': best_k,
        'y_test': y_test,
        'y_pred': best_pred
    }

def cross_validation_test(X, y, metric_name, distance_metric, normalize=True):
    """使用交叉驗證測試"""
    print(f"\n{metric_name} - 交叉驗證 (5折)...")
    
    # 特徵歸一化
    if normalize and distance_metric != 'chi2':
        scaler = StandardScaler()
        X_normalized = scaler.fit_transform(X)
    else:
        X_normalized = X
    
    # 測試不同的 k 值
    k_values = [1, 3, 5]
    cv_results = {}
    
    skf = StratifiedKFold(n_splits=min(5, len(y)//2), shuffle=True, random_state=42)
    
    for k in k_values:
        if distance_metric == 'chi2':
            knn = KNeighborsClassifier(n_neighbors=k, metric=chi_square_distance_sklearn)
        else:
            knn = KNeighborsClassifier(n_neighbors=k, metric=distance_metric)
        scores = cross_val_score(knn, X_normalized, y, cv=skf, scoring='accuracy')
        cv_results[k] = {
            'mean': scores.mean(),
            'std': scores.std(),
            'scores': scores
        }
    
    # 選擇最佳 k
    best_k = max(cv_results.items(), key=lambda x: x[1]['mean'])[0]
    
    return cv_results, best_k

def plot_detailed_results(results, cv_results):
    """繪製詳細結果"""
    print("\n生成詳細分析圖表...")
    
    # 創建大型圖表
    fig = plt.figure(figsize=(16, 12))
    
    # 設置中文字體
    try:
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial']
        plt.rcParams['axes.unicode_minus'] = False
    except:
        pass
    
    # 1. 準確率對比
    ax1 = plt.subplot(3, 3, 1)
    metrics_names = list(results.keys())
    accuracies = [results[m]['accuracy'] for m in metrics_names]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    bars = ax1.bar(metrics_names, accuracies, color=colors)
    ax1.set_ylabel('準確率', fontsize=12)
    ax1.set_title('準確率對比', fontsize=14, fontweight='bold')
    ax1.set_ylim([0, 1.1])
    ax1.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars, accuracies):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
               f'{val:.3f}', ha='center', va='bottom', fontsize=10)
    
    # 2. 精確率對比
    ax2 = plt.subplot(3, 3, 2)
    precisions = [results[m]['precision'] for m in metrics_names]
    bars = ax2.bar(metrics_names, precisions, color=colors)
    ax2.set_ylabel('精確率', fontsize=12)
    ax2.set_title('精確率對比', fontsize=14, fontweight='bold')
    ax2.set_ylim([0, 1.1])
    ax2.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars, precisions):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
               f'{val:.3f}', ha='center', va='bottom', fontsize=10)
    
    # 3. 召回率對比
    ax3 = plt.subplot(3, 3, 3)
    recalls = [results[m]['recall'] for m in metrics_names]
    bars = ax3.bar(metrics_names, recalls, color=colors)
    ax3.set_ylabel('召回率', fontsize=12)
    ax3.set_title('召回率對比', fontsize=14, fontweight='bold')
    ax3.set_ylim([0, 1.1])
    ax3.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars, recalls):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
               f'{val:.3f}', ha='center', va='bottom', fontsize=10)
    
    # 4-6. 混淆矩陣
    for idx, (metric_name, result) in enumerate(results.items()):
        ax = plt.subplot(3, 3, 4 + idx)
        cm = result['confusion_matrix']
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=['不在床', '在床'],
                   yticklabels=['不在床', '在床'],
                   ax=ax, cbar=False)
        ax.set_title(f'{metric_name} - 混淆矩陣 (k={result["best_k"]})', 
                    fontsize=12, fontweight='bold')
        ax.set_ylabel('實際')
        ax.set_xlabel('預測')
    
    # 7-9. 交叉驗證結果
    for idx, (metric_name, cv_result) in enumerate(cv_results.items()):
        ax = plt.subplot(3, 3, 7 + idx)
        k_values = list(cv_result.keys())
        means = [cv_result[k]['mean'] for k in k_values]
        stds = [cv_result[k]['std'] for k in k_values]
        
        ax.errorbar(k_values, means, yerr=stds, marker='o', capsize=5, 
                   color=colors[idx], linewidth=2, markersize=8)
        ax.set_xlabel('k 值', fontsize=12)
        ax.set_ylabel('準確率', fontsize=12)
        ax.set_title(f'{metric_name} - 不同k值性能', fontsize=12, fontweight='bold')
        ax.set_ylim([0, 1.1])
        ax.grid(True, alpha=0.3)
        ax.set_xticks(k_values)
    
    plt.suptitle('HOG 特徵檢測詳細分析', fontsize=18, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig('hog_detailed_analysis.png', dpi=300, bbox_inches='tight')
    print("詳細分析圖已保存為: hog_detailed_analysis.png")

def main():
    print("=" * 70)
    print("HOG 特徵檢測測試程序 - 進階版")
    print("=" * 70)
    
    # 載入特徵
    features_data = load_features('features.json')
    
    # 準備數據集
    X, y, features_data = prepare_dataset(features_data)
    
    # 檢查數據集大小
    if len(X) < 10:
        print("\n警告: 數據集太小，結果可能不可靠")
    
    # 測試不同的距離度量
    distance_metrics = {
        'L1 (Manhattan)': 'manhattan',
        'L2 (Euclidean)': 'euclidean',
        'Chi-square': 'chi2'  # 注意：需要非負特徵
    }
    
    results = {}
    cv_results = {}
    
    print("\n" + "=" * 70)
    print("開始測試 (使用特徵歸一化)...")
    print("=" * 70)
    
    # 先對 Chi-square 做特殊處理（需要非負特徵）
    X_nonneg = X - X.min() + 1e-10  # 確保所有特徵非負
    
    for name, metric in distance_metrics.items():
        print(f"\n{'='*70}")
        print(f"測試 {name} 距離")
        print('='*70)
        
        # 選擇合適的數據
        X_use = X_nonneg if metric == 'chi2' else X
        
        # 單次分割測試
        result = test_with_normalization(X_use, y, name, metric, normalize=True)
        results[name] = result
        
        print(f"\n最佳 k 值: {result['best_k']}")
        print(f"準確率: {result['accuracy']:.4f} ({result['accuracy']*100:.2f}%)")
        print(f"精確率: {result['precision']:.4f}")
        print(f"召回率: {result['recall']:.4f}")
        print(f"F1 分數: {result['f1']:.4f}")
        
        # 交叉驗證
        cv_res, best_k = cross_validation_test(X_use, y, name, metric, normalize=True)
        cv_results[name] = cv_res
        
        print(f"\n交叉驗證最佳 k 值: {best_k}")
        for k, scores in cv_res.items():
            print(f"  k={k}: {scores['mean']:.4f} (+/- {scores['std']:.4f})")
    
    # 性能總結
    print("\n" + "=" * 70)
    print("性能總結 (使用歸一化)")
    print("=" * 70)
    print(f"{'距離度量':<20} {'最佳k':<8} {'準確率':<12} {'精確率':<12} {'召回率':<12} {'F1':<12}")
    print("-" * 70)
    
    for name, result in results.items():
        print(f"{name:<20} {result['best_k']:<8} {result['accuracy']:<12.4f} "
              f"{result['precision']:<12.4f} {result['recall']:<12.4f} {result['f1']:<12.4f}")
    
    # 找出最佳方法
    best_method = max(results.items(), key=lambda x: x[1]['accuracy'])
    print("\n" + "=" * 70)
    print(f"最佳方法: {best_method[0]}")
    print(f"  準確率: {best_method[1]['accuracy']:.4f}")
    print(f"  最佳 k 值: {best_method[1]['best_k']}")
    print("=" * 70)
    
    # 詳細分類報告
    print("\n詳細分類報告 (最佳方法):")
    print("-" * 70)
    print(classification_report(
        best_method[1]['y_test'], 
        best_method[1]['y_pred'],
        target_names=['不在床', '在床'],
        zero_division=0
    ))
    
    # 繪製詳細結果
    try:
        plot_detailed_results(results, cv_results)
        print("\n✓ 圖表生成成功")
    except Exception as e:
        print(f"\n注意: 無法生成圖表 - {e}")
    
    # 數據集建議
    print("\n" + "=" * 70)
    print("建議:")
    print("=" * 70)
    if len(X) < 50:
        print("• 數據集較小，建議收集更多樣本以提高模型可靠性")
        print("• 建議每類至少 30-50 個樣本")
    
    print("• 考慮使用更複雜的特徵（如 SIFT, SURF）或深度學習方法")
    print("• 可以嘗試特徵降維（PCA）來減少計算複雜度")
    
    print("\n測試完成！")

if __name__ == "__main__":
    main()

