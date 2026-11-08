"""Protocol constants and encoders for Honda generator BLE.

All values are documented in ``docs/PROTOCOL.md``. Nothing here is manufacturer code;
these are facts about the wire protocol plus original helpers.
"""
from __future__ import annotations

import enum

# --- Remote Control service -------------------------------------------------
REMOTE_CONTROL_SERVICE = "066b0001-5d90-4939-a7ba-7b9222f53e81"
ENGINE_CONTROL_CHAR = "066b0002-5d90-4939-a7ba-7b9222f53e81"   # write 0x01/0x00
ENGINE_DRIVE_STATUS_CHAR = "066b0003-5d90-4939-a7ba-7b9222f53e81"  # notify
CONTROL_SEQ_CONFIG_CHAR = "066b0004-5d90-4939-a7ba-7b9222f53e81"
FRAME_NUMBER_CHAR = "066b0005-5d90-4939-a7ba-7b9222f53e81"      # read serial
UNLOCK_CHAR = "066b0006-5d90-4939-a7ba-7b9222f53e81"           # write 9 bytes
CHANGE_PASSWORD_CHAR = "066b0007-5d90-4939-a7ba-7b9222f53e81"

# --- Generator Data service -------------------------------------------------
GENERATOR_DATA_SERVICE = "01b60001-875a-4c56-b8bf-5103cafaeec7"
DATA_REQUEST_CHAR = "01b60002-875a-4c56-b8bf-5103cafaeec7"      # write
DATA_RESPONSE_CHAR = "01b60003-875a-4c56-b8bf-5103cafaeec7"     # notify
CAN_DATA_DRIP_CHAR = "01b60004-875a-4c56-b8bf-5103cafaeec7"     # notify
ERROR_WARNING_CHAR = "01b60005-875a-4c56-b8bf-5103cafaeec7"     # notify

# --- Diagnostic service -----------------------------------------------------
DIAGNOSTIC_SERVICE = "b4ef0001-62d2-483c-8293-119e2a99a82b"
FIRMWARE_VERSION_CHAR = "b4ef0004-62d2-483c-8293-119e2a99a82b"

# --- BT-unit Control service (newer "Z45A" generators) ----------------------
# These units ship with a per-unit password printed beside a QR code on the
# generator, NOT the "00000000" default. The unlock payload is the same 9-byte
# format, but it is written to BT_UNIT_UNLOCK_CHAR below.
BT_UNIT_SERVICE = "92cd0001-4f59-4599-a73c-c92c4ac7aade"
BT_UNIT_UNLOCK_CHAR = "92cd0002-4f59-4599-a73c-c92c4ac7aade"
BT_UNIT_CHANGE_PASSWORD_CHAR = "92cd0003-4f59-4599-a73c-c92c4ac7aade"
BT_UNIT_FRAME_NUMBER_CHAR = "92cd0007-4f59-4599-a73c-c92c4ac7aade"

DEFAULT_PASSWORD = "00000000"

# Some units (the EU7000isN, at least) don't advertise their service UUIDs. They show up under the model part
# of their serial number instead, e.g. "EEJD" for the EU7000is.
NAME_PREFIXES = ("EEJD",)

# Engine control payloads.
START = bytes([0x01])
STOP = bytes([0x00])


class Permission(enum.IntEnum):
    """First byte of an unlock write."""
    OWNER = 0x01
    GUEST = 0x02
    RESET = 0x03


class EngineState(enum.IntEnum):
    """Value reported on the engine-drive-status characteristic."""
    WAITING = 0
    STARTING = 1
    RUNNING = 2
    STOPPED = 3


def engine_running(data: bytes) -> bool | None:
    """Whether the engine is running, from an engine-drive-status value.

    The EU7000isN sends 4 bytes and the second is the run flag (``00 01 00 90`` running,
    ``00 00 00 72`` stopped; the other bytes aren't explained yet). The 1-byte form is
    :class:`EngineState`.
    """
    if not data:
        return None
    if len(data) >= 2:
        return data[1] != 0
    return data[0] in (EngineState.STARTING, EngineState.RUNNING)


# CAN message IDs seen on the data-response characteristic (decimal).
# Field byte layouts are not yet confirmed — see docs/PROTOCOL.md section 4.1.
CAN_ECU_STATUS = 786        # 0x312  eco switch, fuel-remaining level
CAN_INVERTER_STATUS = 802   # 0x322
CAN_INVERTER_INFO = 818     # 0x332  output power, current, voltage
CAN_INVERTER_INFO2 = 850    # 0x352  engine hours
CAN_ECU_INFO_ETC = 866      # 0x362  fuel remaining (time), fuel level
CAN_OUTPUT_SETTING = 1490   # 0x5D2  output voltage setting


def build_unlock(password: str = DEFAULT_PASSWORD,
                 permission: Permission = Permission.OWNER) -> bytes:
    """Build the 9-byte unlock payload.

    Layout: [permission, p0..p7] where p0..p7 are the password as ASCII bytes,
    zero-padded to 8. Passwords longer than 8 characters are rejected.
    """
    if permission == Permission.RESET:
        raise ValueError("reset unlock uses a different encoding; not supported here")
    pw = password.encode("ascii")
    if len(pw) > 8:
        raise ValueError("password must be at most 8 characters")
    payload = bytearray(9)
    payload[0] = int(permission)
    payload[1:1 + len(pw)] = pw
    return bytes(payload)
