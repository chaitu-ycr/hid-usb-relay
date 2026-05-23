"""FastAPI application surface for HID USB relay control."""

from typing import Literal, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from hid_usb_relay.usb_relay import RelayError, RelayService


class RelayAPI:
    """Owns application wiring and endpoint handlers."""

    def __init__(self) -> None:
        self.service = RelayService()
        self.app = FastAPI(title='HID USB Relay API', version='26.1.0')
        self._bind_routes()

    def _guard(self, fn, *args, status_code: int = 400):
        try:
            return fn(*args)
        except RelayError as exc:
            raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    def _bind_routes(self) -> None:
        app = self.app

        @app.get('/')
        def root() -> dict:
            return {'status': 'ok', 'message': 'HID USB Relay API', 'routes': {'health': '/health', 'devices': '/api/v1/devices', 'relay_control': '/api/v1/relay/control', 'relay_state': '/api/v1/relay/state'}}

        @app.get('/health')
        @app.get('/api/v1/health')
        def health_check() -> dict:
            devices = self._guard(self.service.get_devices, status_code=503)
            return {'status': 'ok', 'device_count': len(devices)}

        @app.get('/api/v1/devices')
        def list_relay_devices() -> dict:
            devices = self._guard(self.service.get_devices, status_code=503)
            return {'status': 'success', 'count': len(devices), 'devices': devices}

        @app.get('/api/v1/relay/control')
        def relay_control_get(relay_number: str = Query(..., description='1-8 or all'), relay_state: Literal['on', 'off'] = Query(...), relay_id: Optional[str] = Query(None)) -> dict:
            result = self._guard(self.service.set_and_get_relay_state, relay_id, relay_number, relay_state)
            return {'status': 'success', 'relay_state': result.relay_state}

        @app.post('/api/v1/relay/control')
        def relay_control(payload: RelayControlRequest) -> dict:
            result = self._guard(self.service.set_and_get_relay_state, payload.relay_id, payload.relay_number, payload.relay_state)
            return {'status': 'success', 'relay_state': result.relay_state}

        @app.get('/api/v1/relay/state')
        def relay_state_get(relay_number: str = Query(..., description='1-8 or all'), relay_id: Optional[str] = Query(None)) -> dict:
            result = self._guard(self.service.get_state, relay_id, relay_number)
            return {'status': 'success', 'relay_state': result.relay_state}

        @app.post('/api/v1/relay/state')
        def relay_state(payload: RelayReadRequest) -> dict:
            result = self._guard(self.service.get_state, payload.relay_id, payload.relay_number)
            return {'status': 'success', 'relay_state': result.relay_state}


class RelayControlRequest(BaseModel):
    relay_id: Optional[str] = Field(default=None)
    relay_number: str = Field(description='1-8 or all')
    relay_state: Literal['on', 'off']


class RelayReadRequest(BaseModel):
    relay_id: Optional[str] = Field(default=None)
    relay_number: str = Field(description='1-8 or all')


_API = RelayAPI()
app = _API.app


def run_api(host: str = '0.0.0.0', port: int = 9400) -> None:
    """Run API server using uvicorn."""

    uvicorn.run(app, host=host, port=port)
