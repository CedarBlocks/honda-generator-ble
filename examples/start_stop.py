"""Engine start/stop example — USE WITH CARE.

!!  DANGER  !!
Starting a generator runs an internal-combustion engine. Carbon monoxide can kill.
Only run this with the generator's exhaust safely vented, with no one working on the
machine, and ideally with a person watching it. This script deliberately requires
you to be physically present by making you type a confirmation each time.

This library adds NO safety interlock of its own. You are responsible for crank
limiting, run-time limits, CO safety, and a physical override.

Usage:
    python examples/start_stop.py start 12345678
    python examples/start_stop.py stop  12345678
"""
import asyncio
import sys

from honda_generator_ble import GeneratorClient


async def main(action: str, password: str) -> None:
    devices = await GeneratorClient.discover(timeout=10.0)
    if not devices:
        print("No generator found.")
        return

    async with GeneratorClient(devices[0], password=password) as gen:
        await gen.unlock()
        if action == "start":
            confirm = input("Type 'START' to confirm you can see the generator: ")
            if confirm.strip() != "START":
                print("Aborted.")
                return
            await gen.start()
            print("Start command sent.")
        elif action == "stop":
            await gen.stop()
            print("Stop command sent.")
        else:
            print(f"Unknown action: {action!r} (use 'start' or 'stop')")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    act = sys.argv[1]
    pw = sys.argv[2] if len(sys.argv) > 2 else "00000000"
    asyncio.run(main(act, pw))
