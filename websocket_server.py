import websockets
import asyncio
import threading

class WebsocketServer:
    def __init__(self, host='0.0.0.0', port=5501):
        self.host = host
        self.port = port
        self.clients = {}  # 改用字典: websocket -> Connection
        self.loop = None
        self.server_thread = None
        self.running = False

    def register_client(self, websocket):
        connection = Connection(websocket)
        self.clients[websocket] = connection
        print(f"Device connected: {websocket.remote_address}")

    def unregister_client(self, websocket):
        if websocket in self.clients:
            del self.clients[websocket]
            print(f"Device disconnected: {websocket.remote_address}")

    async def send_message(self, websocket, message):
        """發送訊息給單一客戶端"""
        try:
            await websocket.send(message)
            print(f"Sent to {websocket.remote_address}: {message}")
        except Exception as e:
            print(f"Failed to send message: {e}")

    async def receive_message(self, websocket):
        """接收來自客戶端的訊息"""
        async for message in websocket:
            print(f"Received message from {websocket.remote_address}: {message}")
            await self.send_message(websocket, f"ACK:{message}")

    async def handle_client(self, websocket):
        self.register_client(websocket)
        print(f"Connected clients: {len(self.clients)}")
        self.list_clients()
        try:
            await self.receive_message(websocket)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.unregister_client(websocket)

    def send_to_client(self, message):
        """從其他執行緒安全地發送訊息給客戶端"""
        if not self.loop:
            print("WebSocket server not running")
            return False
        
        if not self.clients:
            print(f"No client connected, message dropped: {message}")
            return False
        
        # 在 WebSocket 的 event loop 中執行發送任務
        asyncio.run_coroutine_threadsafe(self._send_to_first_client(message), self.loop)
        return True
    
    async def _send_to_first_client(self, message):
        """內部方法：發送訊息給第一個連接的客戶端"""
        if self.clients:
            websocket = next(iter(self.clients.keys()))
            await self.send_message(websocket, str(message))
        else:
            print(f"No client connected when trying to send: {message}")

    async def _start_async(self):
        """內部 async 啟動方法"""
        async with websockets.serve(self.handle_client, self.host, self.port):
            print(f"WebSocket server started on {self.host}:{self.port}")
            self.running = True
            
            while self.running:
                await asyncio.sleep(1)

    def _run_event_loop(self):
        """在執行緒中運行事件循環"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._start_async())
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.loop.close()

    def start_in_thread(self):
        """在新執行緒中啟動伺服器"""
        if self.server_thread is not None and self.server_thread.is_alive():
            print("Server is already running")
            return
        
        self.server_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.server_thread.start()
        print("WebSocket server thread started")

    def stop(self):
        """停止伺服器"""
        if self.running:
            self.running = False
            if self.loop:
                self.loop.call_soon_threadsafe(self.loop.stop)
            print("WebSocket server stopped")

    def list_clients(self):
        client_list = [client.address for client in self.clients.values()]
        print(f"Connected clients: {client_list}")
        return list(self.clients.values())
    
class Connection:
    def __init__(self, websocket):
        self.websocket = websocket
        self.address = websocket.remote_address
        self.is_connected = True
    

if __name__ == "__main__":
    # 測試：在執行緒中啟動伺服器
    server = WebsocketServer()
    server.start_in_thread()
    
    # 主執行緒可以繼續做其他事情
    try:
        import time
        print("Main thread is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            # 可以在這裡執行其他任務
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()
        print("Server stopped")