"""Regression probe for the installed upstream connector, without credentials."""
import asyncio
import json
from unittest.mock import patch

import connector
from websockets.asyncio.server import serve


async def main():
    executions = []
    connected = 0
    started = asyncio.Event()
    cancelled = asyncio.Event()
    reconnected = asyncio.Event()

    async def forward(_socket, _node, request):
        executions.append(json.loads(request)["id"])
        started.set()
        try:
            await asyncio.Future()
        finally:
            cancelled.set()

    async def relay(socket):
        nonlocal connected
        connected += 1
        if connected == 1:
            await socket.send('{"id":"disposable-operation"}')
            await started.wait()
            await socket.close(code=1012)
        else:
            reconnected.set()
            await socket.wait_closed()

    async with serve(relay, "127.0.0.1", 0) as server, asyncio.timeout(8):
        port = server.sockets[0].getsockname()[1]
        with patch.object(connector, "forward", forward):
            worker = asyncio.create_task(
                connector.worker("pi", f"ws://127.0.0.1:{port}", "fixture-placeholder")
            )
            try:
                await reconnected.wait()
                assert cancelled.is_set()
                assert executions == ["disposable-operation"]
            finally:
                worker.cancel()
                await asyncio.gather(worker, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
    print("In-flight job cancelled on disconnect; connector reconnected without replay")
