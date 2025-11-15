"""
測試數據庫 API
運行前請確保服務器已啟動：python server.py
"""
import requests
import time

BASE_URL = "http://localhost:5502"

def test_sensor_data():
    """測試獲取最新傳感器數據"""
    print("\n" + "="*50)
    print("📊 測試 1: 獲取最新傳感器數據")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/api/sensor-data/alarm-clock")
    data = response.json()
    
    print(f"狀態: {data.get('status')}")
    if data.get('status') == 'success':
        sensor_data = data.get('sensor_data', {})
        print(f"傳感器數據: {sensor_data}")
        for sensor_id, value in sensor_data.items():
            print(f"  - {sensor_id}: {value}")
    else:
        print(f"錯誤: {data.get('message')}")

def test_sensor_history():
    """測試獲取歷史數據"""
    print("\n" + "="*50)
    print("📜 測試 2: 獲取歷史數據（最近 100 條）")
    print("="*50)
    
    response = requests.get(
        f"{BASE_URL}/api/sensor-history/alarm-clock",
        params={'limit': 100}
    )
    data = response.json()
    
    print(f"狀態: {data.get('status')}")
    print(f"設備 ID: {data.get('device_id')}")
    print(f"記錄數量: {data.get('count')}")
    
    if data.get('count', 0) > 0:
        print("\n最近 5 條記錄:")
        for record in data.get('data', [])[:5]:
            print(f"  [{record['timestamp']}] {record['sensor_id']}: {record['value']}")

def test_sensor_history_filtered():
    """測試獲取特定傳感器的歷史數據"""
    print("\n" + "="*50)
    print("🌡️  測試 3: 獲取溫度歷史（最近 50 條）")
    print("="*50)
    
    response = requests.get(
        f"{BASE_URL}/api/sensor-history/alarm-clock",
        params={'sensor_id': 'temperature', 'limit': 50}
    )
    data = response.json()
    
    print(f"狀態: {data.get('status')}")
    print(f"記錄數量: {data.get('count')}")
    
    if data.get('count', 0) > 0:
        values = [record['value'] for record in data.get('data', [])]
        print(f"溫度範圍: {min(values):.1f}°C ~ {max(values):.1f}°C")

def test_sensor_stats():
    """測試獲取統計數據"""
    print("\n" + "="*50)
    print("📈 測試 4: 獲取溫度統計（最近 24 小時）")
    print("="*50)
    
    response = requests.get(
        f"{BASE_URL}/api/sensor-stats/alarm-clock/temperature",
        params={'hours': 24}
    )
    data = response.json()
    
    print(f"狀態: {data.get('status')}")
    if data.get('status') == 'success':
        stats = data.get('stats', {})
        print(f"時間範圍: 最近 {data.get('hours')} 小時")
        print(f"記錄數量: {stats.get('count')}")
        if stats.get('count', 0) > 0:
            print(f"平均值: {stats.get('average'):.2f}°C")
            print(f"最大值: {stats.get('maximum'):.2f}°C")
            print(f"最小值: {stats.get('minimum'):.2f}°C")

def test_sensor_stats_humidity():
    """測試獲取濕度統計"""
    print("\n" + "="*50)
    print("💧 測試 5: 獲取濕度統計（最近 1 小時）")
    print("="*50)
    
    response = requests.get(
        f"{BASE_URL}/api/sensor-stats/alarm-clock/humidity",
        params={'hours': 1}
    )
    data = response.json()
    
    print(f"狀態: {data.get('status')}")
    if data.get('status') == 'success':
        stats = data.get('stats', {})
        print(f"記錄數量: {stats.get('count')}")
        if stats.get('count', 0) > 0:
            print(f"平均濕度: {stats.get('average'):.1f}%")
            print(f"最高濕度: {stats.get('maximum'):.1f}%")
            print(f"最低濕度: {stats.get('minimum'):.1f}%")

def test_devices():
    """測試獲取設備列表"""
    print("\n" + "="*50)
    print("📱 測試 6: 獲取設備列表")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/api/devices")
    data = response.json()
    
    print(f"狀態: {data.get('status')}")
    if data.get('status') == 'success':
        devices = data.get('devices', [])
        print(f"已連接設備數量: {len(devices)}")
        for device in devices:
            print(f"  - {device}")

def main():
    print("🚀 開始測試數據庫 API")
    print("請確保服務器正在運行：python server.py")
    print("請確保至少有一個 ESP32 設備已連接並上傳數據")
    
    try:
        # 測試設備列表
        test_devices()
        
        # 測試最新數據
        test_sensor_data()
        
        # 測試歷史數據
        test_sensor_history()
        
        # 測試過濾的歷史數據
        test_sensor_history_filtered()
        
        # 測試統計數據
        test_sensor_stats()
        test_sensor_stats_humidity()
        
        print("\n" + "="*50)
        print("✅ 所有測試完成！")
        print("="*50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 無法連接到服務器")
        print("請確保服務器正在運行：python server.py")
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")

if __name__ == "__main__":
    main()

