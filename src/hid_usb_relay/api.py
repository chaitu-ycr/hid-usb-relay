"""FastAPI routes for HID USB relay."""

import logging
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from hid_usb_relay.service import RelayService
from hid_usb_relay.usb_relay import RelayError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["relay"])
service = RelayService()


class RelayControlRequest(BaseModel):
    relay_id: Optional[str] = Field(default=None)
    relay_number: str = Field(description="1-8 or 'all'")
    relay_state: Literal["on", "off"]


class RelayReadRequest(BaseModel):
    relay_id: Optional[str] = Field(default=None)
    relay_number: str = Field(description="1-8 or 'all'")


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok", "device_count": len(service.get_devices())}


@router.get("/devices")
def list_relay_devices() -> dict:
    devices = service.get_devices()
    return {"status": "success", "count": len(devices), "devices": devices}


@router.post("/relay/control")
def relay_control(payload: RelayControlRequest) -> dict:
    try:
        result = service.set_and_get_relay_state(payload.relay_id, payload.relay_number, payload.relay_state)
        return {"status": "success", "relay_state": result.relay_state}
    except RelayError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("relay_control error")
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc


@router.post("/relay/state")
def relay_state(payload: RelayReadRequest) -> dict:
    try:
        result = service.get_state(payload.relay_id, payload.relay_number)
        return {"status": "success", "relay_state": result.relay_state}
    except RelayError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("relay_state error")
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc
