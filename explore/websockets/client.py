#!/usr/bin/env python3

import asyncio
import websockets

async def hello():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
      while True:
        greeting = await websocket.recv()
        print(greeting)

asyncio.get_event_loop().run_until_complete(hello())
