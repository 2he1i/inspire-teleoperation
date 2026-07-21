# Inspire Teleoperation

Standalone Quest hand teleoperation for a six-DOF Inspire dexterous hand.
This repository is a copy-based extraction from XR Teleoperate and excludes
arm, camera, chassis, whole-body control, and recording components.

Data flow:

`Quest landmarks -> dex-retargeting -> Modbus TCP hand commands`

## Layout

- `inspire_teleoperation/main.py`: CLI and runtime orchestration
- `inspire_teleoperation/web_ui.py` and `web/`: local Web console
- `inspire_teleoperation/hand_controller.py`: retargeting and command loop
- `inspire_teleoperation/hand_retargeting.py`: local retargeting setup
- `inspire_teleoperation/dexhand.py`: copied low-level Modbus client
- `inspire_teleoperation/assets/hand_model/`: retargeting model and meshes
- `tests/`: hardware-independent unit tests

The runtime uses `televuer` and `dex-retargeting` as libraries. The Modbus
client is included directly, so no sibling DexterousHand checkout is needed.

From the repository root:

```bash
uv run python -m inspire_teleoperation --help
uv run python -m unittest discover -s tests
uv run python -m inspire_teleoperation
```

The final command can connect hardware. Confirm each host, port, device ID,
the clear workspace, and a conservative speed in the Web console first.
