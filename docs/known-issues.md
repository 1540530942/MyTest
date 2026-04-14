# Known Issues And Mocks

This file records anything that blocks the real chain and the mock used to keep the architecture moving.

## 2026-04-15

| Area | Issue | Current handling | Next step |
| --- | --- | --- | --- |
| Frontend build | `node` and `npm` are not installed in this environment. | Static source was edited and Python-side tests were run. | Install Node.js, then run `npm install` and `npm run build`. |
| MQTT dependency | `paho-mqtt` is not installed globally in this environment. | Added dependency-free core logic and `tests/smoke_chain.py` with an in-memory MQTT mock. | Run `python -m pip install -r device_bridge/pc_serial_bridge/requirements.txt`. |
| MQTT broker | No real broker is confirmed running locally. | Smoke test uses `InMemoryMqttBus`. | Start Mosquitto/EMQX or Docker Compose broker and run bridge against it. |
| Arduino serial | No live Arduino serial port was exercised in this run. | Smoke test uses `MockSerialClient`. | Plug in Arduino Uno, confirm `ARDUINO_PORT`, then run `run_bridge.ps1`. |
| Reboot command | `device_reboot` is not safe or implemented for Arduino Uno bridge. | UI button is disabled and API docs mark it as future work. | Add whitelist, confirmation policy, and firmware support before enabling. |
| GitHub push | GitHub access from this execution environment failed on port 443. | Local commits are preserved; continue local development. | Push manually when network is available: `git push origin feature/personal-domain-visual-control`. |
