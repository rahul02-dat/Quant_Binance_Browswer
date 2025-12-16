import asyncio
import logging
from storage.database import SessionLocal
from storage.repository import TickRepository
from typing import List
from collections import defaultdict

logger = logging.getLogger(__name__)

class TickHandler:
    def __init__(self, batch_size: int = 100, flush_interval: float = 1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer = defaultdict(list)
        self.lock = asyncio.Lock()
        self.running = False
        
    async def start(self):
        self.running = True
        asyncio.create_task(self.periodic_flush())
        
    async def handle_tick(self, tick: dict):
        async with self.lock:
            symbol = tick['symbol']
            self.buffer[symbol].append(tick)
            
            if len(self.buffer[symbol]) >= self.batch_size:
                await self.flush_symbol(symbol)
    
    async def flush_symbol(self, symbol: str):
        if not self.buffer[symbol]:
            return
            
        ticks_to_insert = self.buffer[symbol].copy()
        self.buffer[symbol].clear()
        
        try:
            db = SessionLocal()
            TickRepository.bulk_insert_ticks(db, ticks_to_insert)
            db.close()
            logger.info(f"Flushed {len(ticks_to_insert)} ticks for {symbol}")
        except Exception as e:
            logger.error(f"Error flushing ticks: {e}")
            async with self.lock:
                self.buffer[symbol].extend(ticks_to_insert)
    
    async def periodic_flush(self):
        while self.running:
            await asyncio.sleep(self.flush_interval)
            async with self.lock:
                symbols = list(self.buffer.keys())
            
            for symbol in symbols:
                await self.flush_symbol(symbol)
    
    async def stop(self):
        self.running = False
        async with self.lock:
            for symbol in list(self.buffer.keys()):
                await self.flush_symbol(symbol)