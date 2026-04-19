"""WebSocket manager lifecycle and safe-send regression tests."""

import sys
import time
import asyncio
from pathlib import Path

from fastapi.websockets import WebSocketState

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.routes.websocket import WebSocketManager


class FakeWebSocket:
    """Minimal websocket test double for manager tests."""

    def __init__(
        self,
        client_state: WebSocketState,
        application_state: WebSocketState,
        raise_on_send: bool = False,
    ):
        self.client_state = client_state
        self.application_state = application_state
        self.raise_on_send = raise_on_send
        self.sent_messages = []

    async def send_json(self, message):
        if self.raise_on_send:
            raise RuntimeError("send failed")
        self.sent_messages.append(message)


def _metadata(user_id: int):
    now = time.time()
    return {"user_id": user_id, "connected_at": now, "last_heartbeat": now}


def test_send_to_user_prunes_unready_connections():
    manager = WebSocketManager()
    user_id = 101
    ready_ws = FakeWebSocket(WebSocketState.CONNECTED, WebSocketState.CONNECTED)
    unready_ws = FakeWebSocket(WebSocketState.CONNECTED, WebSocketState.DISCONNECTED)

    manager.active_connections[user_id] = [ready_ws, unready_ws]
    manager.connection_metadata[ready_ws] = _metadata(user_id)
    manager.connection_metadata[unready_ws] = _metadata(user_id)
    manager.user_presence[user_id] = "online"

    sent = asyncio.run(
        manager.send_to_user(user_id, {"type": "system", "data": {"ok": True}})
    )

    assert sent is True
    assert manager.active_connections[user_id] == [ready_ws]
    assert len(ready_ws.sent_messages) == 1
    assert unready_ws not in manager.connection_metadata


def test_send_to_user_removes_failed_socket():
    manager = WebSocketManager()
    user_id = 102
    failing_ws = FakeWebSocket(
        WebSocketState.CONNECTED,
        WebSocketState.CONNECTED,
        raise_on_send=True,
    )

    manager.active_connections[user_id] = [failing_ws]
    manager.connection_metadata[failing_ws] = _metadata(user_id)
    manager.user_presence[user_id] = "online"

    sent = asyncio.run(
        manager.send_to_user(user_id, {"type": "system", "data": {"ok": True}})
    )

    assert sent is False
    assert user_id not in manager.active_connections
    assert manager.user_presence[user_id] == "offline"
    assert failing_ws not in manager.connection_metadata


def test_handle_heartbeat_disconnects_closed_socket():
    manager = WebSocketManager()
    user_id = 103
    closed_ws = FakeWebSocket(WebSocketState.CONNECTED, WebSocketState.DISCONNECTED)

    manager.active_connections[user_id] = [closed_ws]
    manager.connection_metadata[closed_ws] = _metadata(user_id)
    manager.user_presence[user_id] = "online"

    asyncio.run(manager.handle_heartbeat(closed_ws))

    assert user_id not in manager.active_connections
    assert manager.user_presence[user_id] == "offline"
    assert closed_ws not in manager.connection_metadata
