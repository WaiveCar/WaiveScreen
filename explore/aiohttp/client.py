#!/usr/bin/env python3
from aiohttp import web
import aiohttp
import time

_conn = None

async def websocket_handler(request):
  global _conn
  ws = web.WebSocketResponse()
  await ws.prepare(request)

  _conn = ws
  async for msg in ws:
    if msg.type == aiohttp.WSMsgType.TEXT:
      if msg.data == 'close':
        await ws.close()
      else:
        await ws.send_str(msg.data + '/answer')

    elif msg.type == aiohttp.WSMsgType.ERROR:
      print('ws connection closed with exception %s' %
        ws.exception())

  print('websocket connection closed')

  return ws

async def index_handler(request):
  await _conn.send_str("surprise")
  return web.Response( text="Hello")

def init_func(argv):
    app = web.Application()
    app.add_routes([
      web.get('/', index_handler),
      web.get('/ws', websocket_handler)
    ])
    return app
