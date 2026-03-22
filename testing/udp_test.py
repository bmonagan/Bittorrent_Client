import asyncio

class UDPServerProtocol(asyncio.DatagramProtocol):
    transport: asyncio.DatagramTransport | None

    def __init__(self):
        super().__init__()
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print("UDP server listening on 0.0.0.0:5005")

    def datagram_received(self, data, addr):
        print(f"Received {data!r} from {addr}")
        if self.transport is not None:
            self.transport.sendto(data, addr)  # Echo back

    def error_received(self, exc):
        print(f"UDP error received: {exc}")

    def connection_lost(self, exc):
        print("UDP server closed")

async def main():
    loop = asyncio.get_running_loop()
    transport = None
    try:
        transport, _ = await loop.create_datagram_endpoint(
            UDPServerProtocol,
            local_addr=("0.0.0.0", 5005)
        )
        await asyncio.sleep(30)  # Run for 30s
    except asyncio.CancelledError:
        # Cancellation is expected during shutdown.
        pass
    finally:
        if transport is not None:
            transport.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user")