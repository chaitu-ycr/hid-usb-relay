"""FastAPI routes for HID USB relay."""

from typing import Literal, Optional

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

__all__ = ["HIDUSBRelayAPI", "app", "run_api"]

from hid_usb_relay.usb_relay import RelayError, RelayService


class HIDUSBRelayAPI:
    class RelayControlRequest(BaseModel):
        relay_id: Optional[str] = Field(default=None)
        relay_number: str = Field(description="1-8 or 'all'")
        relay_state: Literal["on", "off"]

    class RelayReadRequest(BaseModel):
        relay_id: Optional[str] = Field(default=None)
        relay_number: str = Field(description="1-8 or 'all'")

    def __init__(self) -> None:
        self.service = RelayService()
        self.root_router = APIRouter(tags=["root"])
        self.router = APIRouter(prefix="/api/v1", tags=["relay"])
        self.app = FastAPI(
            title="HID USB Relay API",
            version="26.1.0",
            description="API server for controlling HID USB relay devices.",
        )
        self._register_routes()
        self.app.include_router(self.root_router)
        self.app.include_router(self.router)

    def _register_routes(self) -> None:
        self.root_router.get("/")(self.root)
        self.root_router.get("/health")(self.health_check_root)

        self.router.get("/health")(self.health_check)
        self.router.get("/devices")(self.list_relay_devices)
        self.router.get("/relay/control")(self.relay_control_get)
        self.router.post("/relay/control")(self.relay_control)
        self.router.get("/relay/state")(self.relay_state_get)
        self.router.post("/relay/state")(self.relay_state)

    def root(self) -> dict:
        return {
            "status": "ok",
            "message": "HID USB Relay API",
            "routes": {
                "health": "/health",
                "devices": "/api/v1/devices",
                "relay_control": "/api/v1/relay/control",
                "relay_state": "/api/v1/relay/state",
            },
        }

    def health_check_root(self) -> dict:
        return {"status": "ok", "device_count": len(self.service.get_devices())}

    def health_check(self) -> dict:
        return {"status": "ok", "device_count": len(self.service.get_devices())}

    def list_relay_devices(self) -> dict:
        devices = self.service.get_devices()
        return {"status": "success", "count": len(devices), "devices": devices}

    def relay_control_get(
        self,
        relay_number: str = Query(..., description="1-8 or 'all'"),
        relay_state: Literal["on", "off"] = Query(..., description="Relay state"),
        relay_id: Optional[str] = Query(None, description="Optional relay device id"),
    ) -> dict:
        try:
            result = self.service.set_and_get_relay_state(relay_id, relay_number, relay_state)
            return {"status": "success", "relay_state": result.relay_state}
        except RelayError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Internal Server Error") from exc

    def relay_control(self, payload: RelayControlRequest) -> dict:
        try:
            result = self.service.set_and_get_relay_state(
                payload.relay_id,
                payload.relay_number,
                payload.relay_state,
            )
            return {"status": "success", "relay_state": result.relay_state}
        except RelayError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Internal Server Error") from exc

    def relay_state_get(
        self,
        relay_number: str = Query(..., description="1-8 or 'all'"),
        relay_id: Optional[str] = Query(None, description="Optional relay device id"),
    ) -> dict:
        try:
            result = self.service.get_state(relay_id, relay_number)
            return {"status": "success", "relay_state": result.relay_state}
        except RelayError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Internal Server Error") from exc

    def relay_state(self, payload: RelayReadRequest) -> dict:
        try:
            result = self.service.get_state(payload.relay_id, payload.relay_number)
            return {"status": "success", "relay_state": result.relay_state}
        except RelayError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Internal Server Error") from exc

    def run_api(self, host: str = "0.0.0.0", port: int = 9400) -> None:
        uvicorn.run(self.app, host=host, port=port)


_api = HIDUSBRelayAPI()
app = _api.app
run_api = _api.run_api
