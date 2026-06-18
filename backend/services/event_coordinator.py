import asyncio
import json
from typing import Callable, Dict, Any, List

class EventCoordinator:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self._queue = asyncio.Queue()

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    async def publish(self, event_type: str, payload: Dict[str, Any]):
        await self._queue.put({"type": event_type, "payload": payload})

    async def start_listening(self):
        while True:
            event = await self._queue.get()
            event_type = event["type"]
            payload = event["payload"]
            
            if event_type in self.subscribers:
                for handler in self.subscribers[event_type]:
                    # Ideally dispatch to a thread pool or create task for concurrent execution
                    asyncio.create_task(self._safe_execute(handler, payload))
            
            self._queue.task_done()

    async def _safe_execute(self, handler: Callable, payload: Dict[str, Any]):
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(payload)
            else:
                handler(payload)
        except Exception as e:
            print(f"[EventCoordinator] Error handling event: {e}")

# Global singleton
event_bus = EventCoordinator()
