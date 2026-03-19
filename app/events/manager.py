"""Event manager for handling lamp events."""

import asyncio
from typing import Callable, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from loguru import logger


class EventType(str, Enum):
    """Event types."""
    GATEWAY_CONNECTED = "gateway_connected"
    GATEWAY_DISCONNECTED = "gateway_disconnected"
    LAMP_STATE_CHANGED = "lamp_state_changed"
    LAMP_ADDED = "lamp_added"
    LAMP_REMOVED = "lamp_removed"
    ERROR = "error"


@dataclass
class Event:
    """Base event class."""
    type: EventType
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    data: Dict[str, Any] = field(default_factory=dict)


EventHandler = Callable[[Event], None]


class EventManager:
    """Event manager for publishing and subscribing to events."""

    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {
            event_type: [] for event_type in EventType
        }
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe to an event type."""
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug(f"Subscribed to {event_type}")

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe from an event type."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Unsubscribed from {event_type}")

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        await self._event_queue.put(event)
        logger.debug(f"Published event: {event.type}")

    async def start(self) -> None:
        """Start event processing loop."""
        self._running = True
        asyncio.create_task(self._process_loop())
        logger.info("Event manager started")

    async def stop(self) -> None:
        """Stop event processing loop."""
        self._running = False
        logger.info("Event manager stopped")

    async def _process_loop(self) -> None:
        """Process events from queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                await self._dispatch(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event processing error: {e}")

    async def _dispatch(self, event: Event) -> None:
        """Dispatch event to handlers."""
        handlers = self._handlers.get(event.type, [])

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Handler error for {event.type}: {e}")
