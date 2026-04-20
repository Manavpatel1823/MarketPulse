"""Async event bus for streaming simulation progress to WebSocket clients.

The SimulationEngine emits typed events at key points. Zero or more
WebSocket handlers subscribe via `listen()` and receive events as they
happen. If no one is listening the events are silently dropped — the bus
adds zero overhead to CLI-only runs.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    # Setup
    SIM_STARTED = "sim_started"
    AGENT_CREATED = "agent_created"
    AGENTS_READY = "agents_ready"

    # Opinion phase
    OPINION_FORMED = "opinion_formed"
    OPINIONS_DONE = "opinions_done"

    # Debate phase
    ROUND_STARTED = "round_started"
    DEBATE_START = "debate_start"
    DEBATE_RESULT = "debate_result"
    CONVERSION = "conversion"
    ROUND_COMPLETE = "round_complete"

    # Reflection
    REFLECTION_DONE = "reflection_done"

    # Final
    REPORT_STARTED = "report_started"
    REPORT_READY = "report_ready"
    SIM_COMPLETE = "sim_complete"
    SIM_ERROR = "sim_error"


@dataclass
class SimEvent:
    type: EventType
    data: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({"type": self.type.value, "data": self.data}, default=str)


class EventBus:
    """Fan-out event bus backed by asyncio.Queue per subscriber."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[SimEvent]] = []

    def subscribe(self) -> asyncio.Queue[SimEvent]:
        """Register a new subscriber. Returns a Queue to read events from."""
        q: asyncio.Queue[SimEvent] = asyncio.Queue()
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[SimEvent]) -> None:
        """Remove a subscriber."""
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass

    async def emit(self, event: SimEvent) -> None:
        """Push an event to all subscribers (non-blocking put)."""
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass  # slow consumer — drop rather than block the engine

    @property
    def has_subscribers(self) -> bool:
        return len(self._subscribers) > 0
