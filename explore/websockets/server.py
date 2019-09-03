#!/usr/bin/env python3

# WS server example

import asyncio
import websockets
import time

async def hello(websocket, path):
    for i in range(0,4):
      await websocket.send("{}".format(i))
      time.sleep(2)


start_server = websockets.serve(hello, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
