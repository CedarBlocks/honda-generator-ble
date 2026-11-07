# Contributing

Thanks for helping other off-grid generator owners.

## What we most need

1. **Live data-field captures.** The BLE telemetry message IDs are known, but the
   byte offset and scaling of each value (fuel %, output watts, engine hours) still
   need confirming on real hardware. See `docs/PROTOCOL.md` section 4.1 for how to
   capture them with an Android HCI snoop log and Wireshark. A few rows per field,
   with your generator model, is enough.

2. **The serial / QR-password question.** Confirm, per model, whether the generator
   firmware accepts engine control after an unlock alone, and how the QR-code
   password maps to the unlock bytes. Report your model and result.

3. **Model coverage.** Which service (`066B…` classic vs `92CD…` Z45A) your unit
   uses, and whether start/stop works.

## Ground rules

- **No manufacturer code or binaries** in the repo or PRs — no APKs, decompiled
  sources, firmware, or app assets. This project documents the wire protocol for
  interoperability only. Keep it that way so it stays clean-room.
- **Redact personal data** from any logs you attach (your serial number is yours;
  a field's raw bytes and the matching displayed value are what we need).
- Be careful with start/stop testing. See the safety section of the README.

## Dev setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e . bleak
python examples/read_status.py
```
