"""Async BLE client for Honda inverter generators, built on bleak.

Supports both generator families:

* "classic" units — control on the Remote Control service (``066B…``), factory
  default password ``00000000``.
* "Z45A" / BT-unit units — control on the BT-unit service (``92CD…``), with a
  per-unit password printed beside the QR code on the generator.

The client auto-detects which family a connected device is by looking at the GATT
services it advertises.

Read ``docs/PROTOCOL.md`` and the safety section of the README before using
``start()``. Starting a generator remotely is a real-world action with real-world
consequences; this library does not add any safety interlock of its own.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

from . import protocol as P


@dataclass
class _Profile:
    """Which characteristics to use for a given generator family."""
    name: str
    unlock_char: str
    engine_char: str
    status_char: str
    frame_char: str


CLASSIC = _Profile(
    name="classic",
    unlock_char=P.UNLOCK_CHAR,
    engine_char=P.ENGINE_CONTROL_CHAR,
    status_char=P.ENGINE_DRIVE_STATUS_CHAR,
    frame_char=P.FRAME_NUMBER_CHAR,
)

# Z45A units expose the BT-unit service for unlock + frame number, but engine
# control and status still live on the Remote Control service.
Z45A = _Profile(
    name="z45a",
    unlock_char=P.BT_UNIT_UNLOCK_CHAR,
    engine_char=P.ENGINE_CONTROL_CHAR,
    status_char=P.ENGINE_DRIVE_STATUS_CHAR,
    frame_char=P.BT_UNIT_FRAME_NUMBER_CHAR,
)


class GeneratorClient:
    """Connect to one Honda generator over BLE.

    Example::

        async with GeneratorClient(device) as gen:
            await gen.unlock("12345678")   # code beside the QR, or "00000000"
            print(await gen.read_frame_number())
            # await gen.start()            # only with eyes on the machine!
    """

    def __init__(self, device: BLEDevice | str, password: str = P.DEFAULT_PASSWORD):
        self._address = device.address if isinstance(device, BLEDevice) else device
        self._device = device
        self._password = password
        self._client: Optional[BleakClient] = None
        self._profile: Optional[_Profile] = None

    # -- discovery -----------------------------------------------------------
    @staticmethod
    async def discover(timeout: float = 10.0) -> list[BLEDevice]:
        """Return BLE devices that expose a Honda generator control service."""
        found: list[BLEDevice] = []
        devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
        for dev, adv in devices.values():
            uuids = {u.lower() for u in (adv.service_uuids or [])}
            if P.REMOTE_CONTROL_SERVICE in uuids or P.BT_UNIT_SERVICE in uuids:
                found.append(dev)
        return found

    # -- connection ----------------------------------------------------------
    async def __aenter__(self) -> "GeneratorClient":
        await self.connect()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.disconnect()

    async def connect(self) -> None:
        self._client = BleakClient(self._device)
        await self._client.connect()
        self._profile = self._detect_profile()

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.disconnect()
            self._client = None

    def _detect_profile(self) -> _Profile:
        assert self._client is not None
        services = {s.uuid.lower() for s in self._client.services}
        if P.BT_UNIT_SERVICE in services:
            return Z45A
        return CLASSIC

    @property
    def family(self) -> str:
        return self._profile.name if self._profile else "unknown"

    # -- commands ------------------------------------------------------------
    async def unlock(self, password: Optional[str] = None,
                     permission: P.Permission = P.Permission.OWNER) -> None:
        """Authenticate. Must be called before start/stop.

        ``password`` defaults to the one given at construction (``00000000`` if
        unset). For a Z45A unit, pass the 8-character code printed beside the QR.
        """
        self._require_connected()
        payload = P.build_unlock(password or self._password, permission)
        await self._client.write_gatt_char(self._profile.unlock_char, payload, response=True)

    async def start(self) -> None:
        """Start the engine. See the README safety section first."""
        self._require_connected()
        await self._client.write_gatt_char(self._profile.engine_char, P.START, response=True)

    async def stop(self) -> None:
        """Stop the engine."""
        self._require_connected()
        await self._client.write_gatt_char(self._profile.engine_char, P.STOP, response=True)

    async def read_frame_number(self) -> str:
        """Read the generator's serial / frame number."""
        self._require_connected()
        raw = await self._client.read_gatt_char(self._profile.frame_char)
        return raw.decode("ascii", errors="replace").strip("\x00").strip()

    async def watch_engine_state(self, callback) -> None:
        """Subscribe to engine run-state changes.

        ``callback`` is called with a :class:`protocol.EngineState` on each update.
        """
        self._require_connected()

        def _handler(_sender, data: bytearray) -> None:
            if data:
                try:
                    callback(P.EngineState(data[0]))
                except ValueError:
                    callback(data[0])

        await self._client.start_notify(self._profile.status_char, _handler)

    # -- internals -----------------------------------------------------------
    def _require_connected(self) -> None:
        if self._client is None or self._profile is None:
            raise RuntimeError("not connected; call connect() or use 'async with'")


async def _demo() -> None:  # pragma: no cover - manual helper
    devices = await GeneratorClient.discover()
    print(f"found {len(devices)} generator(s)")
    for d in devices:
        print(" ", d.address, d.name)


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(_demo())
