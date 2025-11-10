"""
範例：如何在執行緒中使用 WebSocket 伺服器
"""
import time
from websocket_server import WebsocketServer

def main():
    # 創建伺服器實例
    server = WebsocketServer(host='0.0.0.0', port=5501)
    
    # 在背景執行緒中啟動伺服器
    server.start_in_thread()
    
    print("伺服器已在背景執行緒中啟動")
    print("主程式可以繼續執行其他任務...")
    
    try:
        # 主程式繼續執行其他任務
        counter = 0
        while True:
            time.sleep(2)
            counter += 1
            
            # 檢查連接的客戶端數量
            client_count = len(server.clients)
            print(f"[{counter}] 主程式運行中... 連接客戶端數: {client_count}")
            
            # 如果有客戶端連接，發送訊息
            if client_count > 0:
                message = f"Hello from server! Counter: {counter}"
                server.broadcast_sync(message)
                print(f"已廣播訊息: {message}")
            
            # 每 10 秒顯示連接列表
            if counter % 5 == 0:
                server.list_clients()
                
    except KeyboardInterrupt:
        print("\n正在停止伺服器...")
        server.stop()
        print("伺服器已停止")

if __name__ == "__main__":
    main()


