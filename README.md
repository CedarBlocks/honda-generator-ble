# honda-generator-ble

An independent, open documentation of the Bluetooth Low Energy (BLE) protocol used
by Honda's *My Generator* app to monitor and control Honda inverter generators
(EU7000iS and relatives), plus a small Python reference client.

The goal is **interoperability**: letting owners read and control their own
generator from their own software (a home-automation hub, a Raspberry Pi, a laptop)
instead of being limited to Honda's phone app and its ~75 ft line-of-sight range.

> This project is **not affiliated with, endorsed by, or supported by Honda**.
> "Honda", "EU7000iS", and "My Generator" are trademarks of their respective owner,
> used here only to describe what this project interoperates with.

## Status

| Part | State |
|---|---|
| Service / characteristic UUIDs | **Confirmed** |
| Unlock (password) write | **Confirmed** |
| Engine start / stop write | **Confirmed** |
| Engine run-state notifications | **Confirmed** |
| Data message IDs (fuel, output, engine hours, …) | **Confirmed** |
| Exact byte offsets / scaling of each data value | **Needs live-hardware capture** |
| Role of the panel serial number at the firmware layer | **Open question — see below** |

Everything here was derived by **clean-room documentation of a device's own
protocol for interoperability**. This repository contains **no** manufacturer source
code and **no** app binaries — only facts about the wire protocol and original code.

## Before you start one remotely

Remote-starting an engine over BLE bypasses the wired remote-start interface, so
crank limiting, run-time limits, and an override are on you. Carbon monoxide kills —
only start a generator whose exhaust is safely vented. You accept all risk of using
this software; see `LICENSE`.

## The protocol in one screen

BLE GATT. All multi-byte CAN message IDs below are shown in decimal and hex.

### Control — Remote Control service `066B0001-5D90-4939-A7BA-7B9222F53E81`

| Characteristic | UUID | Use |
|---|---|---|
| Unlock / password | `066B0006-…F53E81` | Write 9 bytes to authenticate (see below) |
| **Engine control** | `066B0002-…F53E81` | Write `0x01` = start, `0x00` = stop |
| Engine drive status | `066B0003-…F53E81` | Notify: `0`=waiting `1`=starting `2`=running `3`=stopped |
| Control-sequence config | `066B0004-…F53E81` | notify config |
| Frame (serial) number | `066B0005-…F53E81` | Read the generator's own serial |
| Change password | `066B0007-…F53E81` | Write a new owner password |

**Unlock write (9 bytes):**

```
[ permission , p0, p1, p2, p3, p4, p5, p6, p7 ]
  permission: 0x01 = owner, 0x02 = guest, 0x03 = reset
  p0..p7:     the password, as 8 ASCII characters
```

The **factory default password is `00000000`** (eight ASCII zeros), so the default
owner unlock is:

```
01 30 30 30 30 30 30 30 30
```

After a successful unlock, write `0x01` to the engine-control characteristic to
start, `0x00` to stop.

### Telemetry — Generator Data service `01B60001-875A-4C56-B8BF-5103CAFAEEC7`

Write a request to `01B60002-…AEEC7`; responses arrive on `01B60003-…AEEC7`.
Payloads are CAN frames identified by these message IDs:

| Message | ID (dec / hex) | Carries |
|---|---|---|
| ECU status | 786 / `0x312` | ECO switch state, fuel-remaining level |
| Inverter status | 802 / `0x322` | inverter state |
| Inverter info | 818 / `0x332` | **output power, output current, output voltage** |
| Inverter info 2 | 850 / `0x352` | **engine hours** |
| ECU info (etc.) | 866 / `0x362` | **fuel remaining (time), fuel level** |
| Output setting | 1490 / `0x5D2` | output voltage setting |
| Insufficient oil | — | low-oil flag |
| Maintenance info | — | maintenance counters |

The *which-field-is-in-which-byte* mapping and scaling factors are not yet confirmed;
`docs/PROTOCOL.md` explains how to capture them from your own generator.

### Other services

- Diagnostic control `B4EF0001-62D2-483C-8293-119E2A99A82B` (command/response + firmware version).
- BT-unit control `92CD0001-4F59-4599-A73C-C92C4AC7AADE` — used by newer "Z45A"
  generators, which derive the password from a QR code rather than using `00000000`.

## Two generator families — and the QR-code password

There are two families, and **which one you have decides your password**:

- **Classic units** — control on the Remote Control service (`066B…`). Factory
  default password `00000000`.
- **Z45A / BT-unit units** — control on the BT-unit service (`92CD…`). These ship
  with a **per-unit password printed beside a QR code** on the generator. During
  setup Honda's app has you scan that QR (or type the number next to it); the part
  after the model prefix **is** the unlock password. It is *not* `00000000`.

If your generator makes you scan a QR code (or enter the number beside it) to pair,
you have a Z45A-type unit: use that code as your password. The 9-byte unlock format
is identical; only the characteristic (`92CD0002` instead of `066B0006`) and the
password value differ. The reference client auto-detects the family on connect.

### The serial-number step

Separately, owners report Honda's app wants the serial ("frame number") from inside
the panel. In the app this is an *ownership check* — it reads the serial from the
device over BLE and also has you enter it, proving you are physically at the machine;
it does not even compare the two. **Not yet confirmed:** whether the generator
*firmware* gates engine control on a serial-derived secret, or whether a correct
unlock is sufficient on its own. Confirming this per model is the top open question —
please open an issue with your result.

## Python reference client

```bash
pip install bleak      # cross-platform BLE
python examples/read_status.py          # read-only: scan, connect, print telemetry
```

See `honda_generator_ble/` for the library and `examples/` for runnable scripts.
Start/stop is in `examples/start_stop.py` and is intentionally guarded.

## Contributing

The most valuable contributions right now are **live captures from real generators**:
the data-field byte layouts, confirmation of the serial-number behavior, and results
across different models. See `docs/PROTOCOL.md` and `CONTRIBUTING.md`.

## License

MIT. See `LICENSE`.
