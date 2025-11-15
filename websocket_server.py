import websockets
import asyncio
import json
import time
import threading

class WebsocketServer:
    def __init__(self, host='0.0.0.0', port=5501, on_sensor_data=None):
        self.host = host
        self.port = port
        self.device_map = {}
        self.sensor_data = {}
        self.loop = None
        self.on_sensor_data = on_sensor_data

    async def handle_client(self, websocket):
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON: {message}")
                    print(f"Error: {e}")
                    continue
                if data["msg_type"] == "register":
                    device_id = data["device_id"]
                    self.device_map[device_id] = websocket
                    print(f"{device_id} connected.")
                    ack = {
                        "msg_type": "registration_ack",
                        "device_id": device_id,
                        "timestamp": int(time.time())
                    }
                    await websocket.send(json.dumps(ack))
                elif data["msg_type"] == "sensor_data":
                    device_id = data["device_id"]
                    sensor_id = data["sensor_id"]
                    value = data["value"]

                    self.sensor_data.setdefault(device_id, {})[sensor_id] = value
                    print(f"{device_id} - {sensor_id}: {value}")
                    if self.on_sensor_data:
                        self.on_sensor_data(device_id, sensor_id, value)
                else:
                    print(f"Unknown message type: {data['msg_type']}")
                    
        except KeyError:
            print(f"KeyError: {data}")
        except Exception as e:
            print(f"Exception: {e}")
        finally:
            if device_id and device_id in self.device_map:
                del self.device_map[device_id]
                print(f"{device_id} disconnected.")
            else:
                print(f"Device {device_id} not found.")
    async def _start_async(self):
        async with websockets.serve(self.handle_client, self.host, self.port):
            print(f"Server started on {self.host}:{self.port}")
            while True:
                await asyncio.sleep(1)

    def start_in_thread(self):
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_until_complete,
                         args=(self._start_async(),),
                         daemon=True).start()
 
    def send_led_command(self, device_id, value):
        cmd = {"msg_type": "led_command", "device_id": device_id, "value": value}
        asyncio.run_coroutine_threadsafe(
            self.device_map[device_id].send(json.dumps(cmd)), self.loop
        )

    def get_sensor_data(self, device_id):
        return self.sensor_data.get(device_id, {})

    def get_device_list(self):
        return list(self.device_map.keys())

if __name__ == "__main__":
    srv = WebsocketServer()
    srv.start_in_thread()