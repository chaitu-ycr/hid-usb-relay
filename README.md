# hid_usb_relay

A Python package for controlling HID USB relay devices with an API, CLI, or desktop GUI.

## Installation

Install from the repository root:

```bash
pip install hid-usb-relay
```

## Command line entry points

Once installed, use one of the provided console scripts:

- `hid-usb-relay-cli` — run the command-line relay interface
- `hid-usb-relay-gui` — launch the Dear PyGui desktop UI
- `hid-usb-relay-api` — start the FastAPI server on `0.0.0.0:9400`

### CLI usage

```bash
hid-usb-relay-cli devices
hid-usb-relay-cli state 1
hid-usb-relay-cli status all
hid-usb-relay-cli control 1 on
hid-usb-relay-cli control all off
```

The CLI commands are:

- `devices` — list connected relay devices
- `state` / `status` — read the current relay state
- `control` — set a relay state to `on` or `off`

Optional device selection is supported with `--relay-id`:

```bash
hid-usb-relay-cli control 1 on --relay-id DEVICE_ID
```

## API usage

Start the API server:

```bash
hid-usb-relay-api
```

The server listens by default on `0.0.0.0:9400`.

### API endpoints

Root endpoints:

- `GET /` — API information
- `GET /health` — health check and connected device count

Relay endpoints:

- `GET /api/v1/devices` — list connected devices
- `GET /api/v1/relay/control?relay_number=1&relay_state=on` — change relay state
- `POST /api/v1/relay/control` — change relay state with JSON payload
- `GET /api/v1/relay/state?relay_number=1` — read relay state
- `POST /api/v1/relay/state` — read relay state with JSON payload

### Example requests

```bash
curl "http://127.0.0.1:9400/health"

curl "http://127.0.0.1:9400/api/v1/devices"

curl "http://127.0.0.1:9400/api/v1/relay/control?relay_number=1&relay_state=on"

curl -X POST "http://127.0.0.1:9400/api/v1/relay/control" \
  -H "Content-Type: application/json" \
  -d '{"relay_number":"1","relay_state":"off"}'

curl "http://127.0.0.1:9400/api/v1/relay/state?relay_number=1"

curl -X POST "http://127.0.0.1:9400/api/v1/relay/state" \
  -H "Content-Type: application/json" \
  -d '{"relay_number":"1"}'
```

## GUI usage

Run the desktop application:

```bash
hid-usb-relay-gui
```

This opens a simple Dear PyGui window for scanning devices, selecting a relay, and toggling relay state.

## Python usage

Import the package in your own Python code:

```python
from hid_usb_relay.usb_relay import USBRelayDevice, RelayState, RelayError, RelayService, enumerate_devices

# List devices
print(enumerate_devices())

# Read relay state
service = RelayService()
result = service.get_state(None, "1")
print(result.relay_state)

# Set relay state
result = service.set_and_get_relay_state(None, "1", "on")
print(result.relay_state)
```

## Notes

- The package uses platform-specific executables from `src/hid_usb_relay/hid_usb_relay_bin`.
- If you do not install the console scripts, you can still import and use `hid_usb_relay.api`, `hid_usb_relay.cli`, and `hid_usb_relay.gui` directly.

## Source manual

For more documentation, see the [source manual](https://chaitu-ycr.github.io/hid-usb-relay/source-manual).
