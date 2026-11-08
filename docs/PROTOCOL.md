# Honda generator BLE protocol

This is an independent description of the BLE GATT protocol used by Honda inverter
generators that work with the *My Generator* app. It was produced by clean-room
documentation for interoperability. It contains no manufacturer code.

Byte values are hex unless noted. UUIDs are written with the shared suffix elided
after the first appearance of each 128-bit base.

## 1. Services and characteristics

### 1.1 Remote Control service

Base UUID suffix: `-5D90-4939-A7BA-7B9222F53E81`

| Name | UUID | Properties | Purpose |
|---|---|---|---|
| Remote Control service | `066B0001-…` | — | container |
| Engine control | `066B0002-…` | write | `01`=start, `00`=stop |
| Engine drive status | `066B0003-…` | read/indicate | engine run-state (§3) |
| Control-sequence config | `066B0004-…` | read/write (EU7000isN) | sequence config |
| Frame (serial) number | `066B0005-…` | read/write (EU7000isN) | device serial string |
| Unlock / password | `066B0006-…` | write | authenticate (§2) |
| Change password | `066B0007-…` | write | set a new owner password |

Finding the device: it's named with the model part of its serial (`EEJD`), so scan by name. A Web Bluetooth scan
showed no service UUIDs in its advertisement, but an iOS BLE app lists `066B0001` as an advertised service (probably
in the scan response), so a scan filtered on `066B0001` may also work. The Generator Data service below is **absent**
on this model; the Diagnostic service is present.

**EU7000isN, as read with an iOS BLE app (engine stopped, unlocked earlier that day):**

| Characteristic | Properties seen | Value read | Notes |
|---|---|---|---|
| `066B0002` | write | — | start/stop (§3) |
| `066B0003` | read, indicate | `00 00 00 72` | stopped (§3) |
| `066B0004` | read, write | `02 3C 28 28 3C` | 5 bytes; meaning unknown (`3C` = 60, `28` = 40: timings?). Unchanged meaning untested; don't write it. |
| `066B0005` | read, write | ASCII serial + 5 null bytes (17 bytes) | e.g. `EEJD-xxxxxxx`; readable by anyone in range |
| `066B0006` | write | — | unlock (§2) |
| `066B0007` | read, write | `00` | the change-password characteristic reads `00` |
| `B4EF0002` | write | — | diagnostic command |
| `B4EF0003` | indicate | `80 01` + ASCII `BB42FF06` + `04` | diagnostic response; meaning unknown |
| `B4EF0004` | read | `10 04` | firmware version |
| `B4EF0005` | write | — | unit operation |

Still to try: read `066B0004` and `066B0007` again while the engine runs, to see if either is live data.

### 1.2 Generator Data service

Base UUID suffix: `-875A-4C56-B8BF-5103CAFAEEC7`

| Name | UUID | Properties | Purpose |
|---|---|---|---|
| Generator Data service | `01B60001-…` | — | container |
| Data request | `01B60002-…` | write | ask for a CAN message |
| Data response | `01B60003-…` | notify | CAN message payload |
| CAN data drip | `01B60004-…` | notify | streamed CAN frames |
| Error / warning info | `01B60005-…` | notify | fault + warning flags |

### 1.3 Diagnostic Control service

Base UUID suffix: `-62D2-483C-8293-119E2A99A82B`

| Name | UUID |
|---|---|
| Diagnostic Control service | `B4EF0001-…` |
| Diagnostic command | `B4EF0002-…` |
| Diagnostic response | `B4EF0003-…` |
| Firmware version | `B4EF0004-…` |
| Unit operation | `B4EF0005-…` |

### 1.4 BT-unit Control service (newer "Z45A" models)

Base UUID suffix: `-4F59-4599-A73C-C92C4AC7AADE`

| Name | UUID |
|---|---|
| BT-unit Control service | `92CD0001-…` |
| Unlock protect | `92CD0002-…` |
| Change password | `92CD0003-…` |
| Unit operation | `92CD0004-…` |
| BT firmware version | `92CD0005-…` |
| CAN firmware version | `92CD0006-…` |
| Frame number | `92CD0007-…` |

Each notify characteristic uses the standard Client Characteristic Configuration
Descriptor `0x2902` to enable notifications.

## 2. Authentication (unlock)

Write **9 bytes** to the unlock characteristic (`066B0006` on classic models,
`92CD0002` on Z45A):

```
byte 0    : permission   0x01 owner, 0x02 guest, 0x03 reset
bytes 1-8 : password, 8 ASCII characters (e.g. "00000000" -> 30 30 30 30 30 30 30 30)
```

- Factory default password (classic units): `00000000`. **Confirmed on an EU7000isN**: `00000000` unlocks
  start/stop, and the serial printed beside the QR sticker does not.
- **Z45A / BT-unit units** (with the `92CD…` service) unlock on `92CD0002` instead; the app suggests a per-unit
  password there. Not yet confirmed on hardware.
- A wrong password is still *accepted* as a write. You only find out when the next reads and writes fail.
- For a `reset` (permission `0x03`) the password field is instead a 3-byte big-endian
  integer parsed from a hex string (reset code), not ASCII.
- Passwords shorter than 8 characters fill only the leading bytes; the rest stay `00`.

Detecting the family: if the device's GATT exposes the BT-unit service
`92CD0001-…`, treat it as Z45A and unlock on `92CD0002`; otherwise use the classic
Remote Control service and `066B0006`. Engine control and status are on the Remote
Control service (`066B0002` / `066B0003`) for both families.

Change the owner password by writing the new password to the change-password
characteristic (`066B0007` / `92CD0003`) after unlocking as owner.

## 3. Engine control and status

- **Start:** write `01` to the engine-control characteristic.
- **Stop:** write `00`.

Both confirmed on an EU7000isN (unlock first).

**EU7000isN engine-drive-status: 4 bytes, readable and indicated.** Byte 1 is the run flag:

| Raw | Meaning |
|---|---|
| `00 01 00 90` | running (still `01` for a few seconds while it spins down) |
| `00 00 00 72` | stopped |

Bytes 0, 2 and 3 aren't explained yet (byte 3 changed between reads). The app's 1-byte form, possibly other
models:

| Value | Meaning |
|---|---|
| `0` | waiting |
| `1` | starting |
| `2` | running |
| `3` | stopped |

There is also a 16-bit "function command" channel seen in the data layer:

| Function | Value (dec / hex) |
|---|---|
| Stop engine | 1026 / `0x402` |
| ECO throttle on | 1027 / `0x403` |
| ECO throttle off | 1028 / `0x404` |

## 4. Telemetry (CAN messages)

Request a message by writing to the data-request characteristic; the device answers
on the data-response characteristic. Each response is a CAN frame tagged with one of
these IDs:

| Message | ID (dec / hex) | Known fields |
|---|---|---|
| ECU status | 786 / `0x312` | ECO switch status, fuel-remaining level |
| Inverter status | 802 / `0x322` | inverter state |
| Inverter info | 818 / `0x332` | output power, output current, output voltage |
| Inverter info 2 | 850 / `0x352` | engine hours |
| ECU info etc. | 866 / `0x362` | fuel remaining (run-time estimate), fuel level |
| Output setting | 1490 / `0x5D2` | output voltage setting |

### 4.1 What still needs confirming

The byte offset, width, endianness, and scale factor of each field inside its CAN
frame are **not yet pinned down**. To capture them from your own generator:

1. On an Android phone, enable **Developer options → Enable Bluetooth HCI snoop log**.
2. Run Honda's app, watch a value change (e.g. let fuel drop, or change output), and
   note the on-screen value and the time.
3. Pull the HCI log (`adb bugreport` or the on-device path) and open it in Wireshark.
4. Filter to the data-response characteristic handle, line up the notification that
   precedes each on-screen value, and solve for offset/scale.
5. Open an issue (or PR to this file) with: generator model, CAN ID, raw bytes, and
   the matching displayed value.

A couple of live rows for each field is enough to lock the scaling for everyone.

## 5. Observed app-level ownership gate (serial number)

Honda's app requires the user to enter or scan the generator's serial ("frame
number", found behind the inside panel) during setup. The app independently reads the
serial from the device over BLE (`066B0005`) but does not compare it to the entered
value — it simply stores the entered one and uses the serial's prefix to pick a model
profile. This reads as an *ownership / anti-theft* step enforced by the app.

**Confirmed on an EU7000isN:** the firmware doesn't use the serial. The unlock password (`00000000`) alone
enables start/stop. Reports from other models are welcome.
