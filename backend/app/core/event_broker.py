"""U0/U4 - 인메모리 EventBroker (인프로세스 Pub/Sub).

토픽:
  - "store:{store_id}:dashboard"  (관리자 대시보드)
  - "session:{session_id}:orders" (고객 주문내역)
이벤트: order.created / order.status_changed / order.deleted / session.ended

주의: 프로세스 인메모리 상태 → backend는 단일 워커로 실행해야 함
(shared-infrastructure.md 참조). 이벤트는 커밋 성공 후에만 publish.
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Event:
    type: str
    data: dict[str, Any]


def dashboard_topic(store_id: uuid.UUID | str) -> str:
    return f"store:{store_id}:dashboard"


def session_topic(session_id: uuid.UUID | str) -> str:
    return f"session:{session_id}:orders"


@dataclass
class _Subscription:
    topic: str
    queue: asyncio.Queue[Event] = field(default_factory=lambda: asyncio.Queue(maxsize=100))


class EventBroker:
    def __init__(self) -> None:
        self._subs: dict[str, set[_Subscription]] = {}

    def subscribe(self, topic: str) -> _Subscription:
        sub = _Subscription(topic=topic)
        self._subs.setdefault(topic, set()).add(sub)
        return sub

    def unsubscribe(self, sub: _Subscription) -> None:
        subs = self._subs.get(sub.topic)
        if subs:
            subs.discard(sub)
            if not subs:
                self._subs.pop(sub.topic, None)

    def publish(self, topic: str, event: Event) -> None:
        """비동기 큐로 팬아웃. 큐가 가득 차면 해당 이벤트는 드롭
        (클라이언트는 재연결 시 스냅샷 재조회로 복구 — last-write-wins)."""
        for sub in list(self._subs.get(topic, ())):
            try:
                sub.queue.put_nowait(event)
            except asyncio.QueueFull:
                pass


# 프로세스 싱글턴
broker = EventBroker()
