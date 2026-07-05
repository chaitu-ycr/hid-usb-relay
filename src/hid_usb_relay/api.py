"""FastAPI application surface for HID USB relay control."""

from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Literal, Optional
import uvicorn

from hid_usb_relay.usb_relay import RelayError, RelayService


class RelayControlRequest(BaseModel):
    """Payload for relay state mutation requests."""

    relay_id: Optional[str] = Field(default=None)
    relay_number: str = Field(description='1-8 or all')
    relay_state: Literal['on', 'off']


class RelayReadRequest(BaseModel):
    """Payload for relay state read requests."""

    relay_id: Optional[str] = Field(default=None)
    relay_number: str = Field(description='1-8 or all')


class RelayAPI:
    """Owns API app lifecycle, routes, and error adaptation."""

    def __init__(self) -> None:
        self.service = RelayService()
        self.app = FastAPI(title='HID USB Relay API', version='26.1.2')
        self._bind_routes()

    def _guard(self, fn: Any, *args: Any, status_code: int = 400) -> Any:
        try:
            return fn(*args)
        except RelayError as exc:
            raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    def _relay_state_response(self, relay_state: object) -> dict[str, object]:
        return {'status': 'success', 'relay_state': relay_state}

    def _bind_routes(self) -> None:
        @self.app.get('/')
        def root() -> dict[str, object]:
            return {
                'status': 'ok',
                'message': 'HID USB Relay API',
                'routes': {
                    'health': '/health',
                    'devices': '/api/v1/devices',
                    'relay_control': '/api/v1/relay/control',
                    'relay_state': '/api/v1/relay/state',
                },
            }

        @self.app.get('/health')
        @self.app.get('/api/v1/health')
        def health_check() -> dict[str, object]:
            devices = self._guard(self.service.get_devices, status_code=503)
            return {'status': 'ok', 'device_count': len(devices)}

        @self.app.get('/api/v1/devices')
        def list_relay_devices() -> dict[str, object]:
            devices = self._guard(self.service.get_devices, status_code=503)
            return {'status': 'success', 'count': len(devices), 'devices': devices}

        @self.app.get('/api/v1/relay/control')
        def relay_control_get(
            relay_number: str = Query(..., description='1-8 or all'),
            relay_state: Literal['on', 'off'] = Query(..., description='Relay state'),
            relay_id: Optional[str] = Query(None, description='Optional relay device id'),
        ) -> dict[str, object]:
            result = self._guard(
                self.service.set_and_get_relay_state,
                relay_id,
                relay_number,
                relay_state,
            )
            return self._relay_state_response(result.relay_state)

        @self.app.post('/api/v1/relay/control')
        def relay_control(payload: RelayControlRequest) -> dict[str, object]:
            result = self._guard(
                self.service.set_and_get_relay_state,
                payload.relay_id,
                payload.relay_number,
                payload.relay_state,
            )
            return self._relay_state_response(result.relay_state)

        @self.app.get('/api/v1/relay/state')
        def relay_state_get(
            relay_number: str = Query(..., description='1-8 or all'),
            relay_id: Optional[str] = Query(None, description='Optional relay device id'),
        ) -> dict[str, object]:
            result = self._guard(self.service.get_state, relay_id, relay_number)
            return self._relay_state_response(result.relay_state)

        @self.app.post('/api/v1/relay/state')
        def relay_state(payload: RelayReadRequest) -> dict[str, object]:
            result = self._guard(self.service.get_state, payload.relay_id, payload.relay_number)
            return self._relay_state_response(result.relay_state)

_API = RelayAPI()
app = _API.app

def run_api(host: str = '0.0.0.0', port: int = 9400) -> None:
    """Run API server using uvicorn."""
    uvicorn.run(app, host=host, port=port)


if __name__ == '__main__':
    run_api()
