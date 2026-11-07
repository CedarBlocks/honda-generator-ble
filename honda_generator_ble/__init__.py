"""honda_generator_ble — an interoperability client for Honda inverter generators.

This package talks to a Honda generator's own BLE GATT interface (the one Honda's
*My Generator* app uses). It is independent of and not endorsed by Honda.

See the module ``protocol`` for UUIDs and command encodings, and ``client`` for an
async client built on bleak. Read ``docs/PROTOCOL.md`` and the safety notes in the
README before using engine start/stop.
"""
from .protocol import (
    REMOTE_CONTROL_SERVICE,
    ENGINE_CONTROL_CHAR,
    ENGINE_DRIVE_STATUS_CHAR,
    UNLOCK_CHAR,
    FRAME_NUMBER_CHAR,
    GENERATOR_DATA_SERVICE,
    DATA_REQUEST_CHAR,
    DATA_RESPONSE_CHAR,
    BT_UNIT_SERVICE,
    BT_UNIT_UNLOCK_CHAR,
    DEFAULT_PASSWORD,
    Permission,
    EngineState,
    build_unlock,
    START,
    STOP,
)
from .client import GeneratorClient

__version__ = "0.1.0"
__all__ = [
    "GeneratorClient",
    "REMOTE_CONTROL_SERVICE",
    "ENGINE_CONTROL_CHAR",
    "ENGINE_DRIVE_STATUS_CHAR",
    "UNLOCK_CHAR",
    "FRAME_NUMBER_CHAR",
    "GENERATOR_DATA_SERVICE",
    "DATA_REQUEST_CHAR",
    "DATA_RESPONSE_CHAR",
    "BT_UNIT_SERVICE",
    "BT_UNIT_UNLOCK_CHAR",
    "DEFAULT_PASSWORD",
    "Permission",
    "EngineState",
    "build_unlock",
    "START",
    "STOP",
]
