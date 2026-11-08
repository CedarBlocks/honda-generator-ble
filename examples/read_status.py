"""Read-only example: find a Honda generator, connect, and print basic info.

This does NOT start or stop the engine. It unlocks (required before most reads on
some units), reads the serial, and watches engine run-state for a few seconds.

Usage:
    pip install bleak
    python examples/read_status.py                 # default password 00000000
    python examples/read_status.py 12345678        # a changed password
"""
import asyncio
import sys

from honda_generator_ble import GeneratorClient


async def main(password: str) -> None:
    print("Scanning for a Honda generator (make sure Honda's app is closed)...")
    devices = await GeneratorClient.discover(timeout=10.0)
    if not devices:
        print("No generator found. Is it powered and in Bluetooth range?")
        return

    device = devices[0]
    print(f"Connecting to {device.name or 'generator'} ({device.address})...")

    async with GeneratorClient(device, password=password) as gen:
        print(f"Connected. Unit family: {gen.family}")
        await gen.unlock()
        print("Unlocked.")

        try:
            serial = await gen.read_frame_number()
            print(f"Serial / frame number: {serial}")
        except Exception as exc:  # noqa: BLE001 - informational only
            print(f"(could not read serial: {exc})")

        running = await gen.is_running()
        print(f"Engine: {'running' if running else 'stopped' if running is not None else 'unknown'}")
        print("Watching engine state for 10s (Ctrl-C to stop)...")
        await gen.watch_engine_state(
            lambda running, raw: print(f"  engine: {'running' if running else 'stopped'} ({raw.hex(' ')})")
        )
        await asyncio.sleep(10)


if __name__ == "__main__":
    pw = sys.argv[1] if len(sys.argv) > 1 else "00000000"
    asyncio.run(main(pw))
