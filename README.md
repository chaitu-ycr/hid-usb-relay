# hid_usb_relay

hid based usb relay package

## Command line entry points

- `hid-usb-relay` — default launcher, use `--mode gui` or `--mode api`
- `hid-usb-relay-gui` — launch the Dear PyGui desktop UI
- `hid-usb-relay-api` — start the FastAPI server on `0.0.0.0:9400`

## API routes

The API server exposes both root and versioned endpoints.

### Root endpoints

- `GET /` — API information
- `GET /health` — health check with device count

### Versioned relay endpoints

- `GET /api/v1/devices` — list connected relay devices
- `GET /api/v1/relay/control?relay_number=1&relay_state=on` — set relay state via query string
- `POST /api/v1/relay/control` — set relay state with JSON payload
- `GET /api/v1/relay/state?relay_number=1` — read relay state via query string
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

## [source manual](https://chaitu-ycr.github.io/hid-usb-relay/source-manual)
