import asyncio
import datetime
import os
import uuid
import nats.aio.client as nats

NATS_URL = os.environ.get("NATS_URL", "nats://localhost:4222")
NATS_QUEUE = os.environ.get("NATS_QUEUE", "queue")
PORT = os.environ.get("PORT", 7298)


def log(msg):
    time = datetime.datetime.now()
    print(f"[{time}]: {msg}")


def in_handler_wrapper(nc):
    async def in_handler(msg):
        log(f"message from queue {msg.subject} sent to out: {msg.data}")
        await nc.publish(msg.reply, msg.data)
        await nc.flush(2)
    return in_handler


def client_handler_wrapper(nc):
    async def client_handler(reader, writer):
        msg = await reader.read()
        client_id = uuid.uuid4()
        log(f"message from client {client_id}: {msg}")
        try:
            resp = await nc.request(NATS_QUEUE, msg, timeout=2)
            await nc.flush(2)
            log(f"response for client {client_id}: {resp.data}")
            writer.write(resp.data)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        except asyncio.TimeoutError:
            log(f"timeout waiting for response for client {client_id}")
    return client_handler


async def main():
    nc = nats.Client()
    await nc.connect(NATS_URL)
    while not nc.is_connected:
        await asyncio.sleep(1)
    log(f"opened nats connection to {NATS_URL}")
    cb = in_handler_wrapper(nc)
    sid = await nc.subscribe(NATS_QUEUE, cb=cb)
    await nc.flush()
    log(f"id of subscription: {sid}")
    server = await asyncio.start_server(client_handler_wrapper(nc), "0.0.0.0", PORT)
    log(f"server start listening at 0.0.0.0:{PORT}")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
