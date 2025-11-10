import websockets
import asyncio

async def connect():
    async with websockets.connect("ws://localhost:5501") as websocket:
        print("Connected to server")
        await websocket.send("Hello, server!")
        response = await websocket.recv()
        print(f"Received response: {response}")

asyncio.run(connect())