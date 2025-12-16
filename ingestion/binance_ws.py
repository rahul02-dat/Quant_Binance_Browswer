import asyncio
import websockets
import json
import logging
from typing import Callable, List
from collections import deque

logger = logging.getLogger(__name__)

class BinanceWebSocket:
    def __init__(self, symbols: List[str], callback: Callable):
        self.symbols = [s.lower() for s in symbols]
        self.callback = callback
        self.ws = None
        self.running = False
        self.buffer = {symbol.upper(): deque(maxlen=10000) for symbol in symbols}
        self.message_count = 0
        
    def get_stream_url(self) -> str:
        streams = [f"{symbol}@trade" for symbol in self.symbols]
        stream_names = "/".join(streams)
        return f"wss://stream.binance.com:9443/stream?streams={stream_names}"
    
    async def connect(self):
        self.running = True
        url = self.get_stream_url()
        logger.info(f"Connecting to Binance WebSocket: {url}")
        
        reconnect_delay = 1
        
        while self.running:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                    self.ws = ws
                    logger.info(f"✓ Connected to Binance WebSocket for {self.symbols}")
                    reconnect_delay = 1
                    
                    while self.running:
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=30.0)
                            data = json.loads(message)
                            await self.process_message(data)
                            self.message_count += 1
                            
                            if self.message_count % 100 == 0:
                                logger.info(f"Processed {self.message_count} messages")
                                
                        except asyncio.TimeoutError:
                            logger.warning("WebSocket receive timeout, sending ping...")
                            try:
                                await ws.ping()
                            except Exception as e:
                                logger.error(f"Ping failed: {e}")
                                break
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket connection closed")
                            break
                        except Exception as e:
                            logger.error(f"Error receiving message: {e}")
                            break
                            
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                if self.running:
                    logger.info(f"Reconnecting in {reconnect_delay} seconds...")
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 30)
    
    async def process_message(self, data: dict):
        try:
            if 'data' not in data:
                logger.debug(f"Received non-data message: {data}")
                return
                
            trade_data = data['data']
            symbol = trade_data['s']
            
            tick = {
                'timestamp': trade_data['T'],
                'symbol': symbol,
                'price': float(trade_data['p']),
                'quantity': float(trade_data['q'])
            }
            
            self.buffer[symbol].append(tick)
            await self.callback(tick)
            
        except KeyError as e:
            logger.error(f"Missing key in trade data: {e}, data: {data}")
        except Exception as e:
            logger.error(f"Error processing message: {e}, data: {data}")
    
    async def stop(self):
        logger.info("Stopping WebSocket client...")
        self.running = False
        if self.ws:
            await self.ws.close()
    
    def get_buffer(self, symbol: str, limit: int = 1000) -> List[dict]:
        if symbol in self.buffer:
            return list(self.buffer[symbol])[-limit:]
        return []
    
    def get_stats(self) -> dict:
        return {
            'total_messages': self.message_count,
            'buffer_sizes': {symbol: len(buffer) for symbol, buffer in self.buffer.items()},
            'is_running': self.running
        }