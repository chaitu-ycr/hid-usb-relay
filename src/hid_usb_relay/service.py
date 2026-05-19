"""Service layer for HID USB relay operations."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from hid_usb_relay.usb_relay import USBRelayDevice, enumerate_devices


@dataclass(frozen=True)
class RelayResult:
    relay_state: Union[str, Dict[str, str]]


class RelayService:
    """Use-case layer that encapsulates relay hardware operations."""

    @staticmethod
    def set_and_get_relay_state(relay_id: Optional[str], relay_number: str, state: str) -> RelayResult:
        relay = USBRelayDevice(device_id=relay_id)
        relay_number_norm = relay_number.strip().lower()
        state_norm = state.strip().lower()

        if relay_number_norm == "all":
            relay.set_state(state_norm)
            return RelayResult(relay_state=relay.get_state())

        relay.set_state(state_norm, relay_number_norm)
        return RelayResult(relay_state=relay.get_relay_state(relay_number_norm))

    @staticmethod
    def get_state(relay_id: Optional[str], relay_number: str) -> RelayResult:
        relay = USBRelayDevice(device_id=relay_id)
        relay_number_norm = relay_number.strip().lower()

        if relay_number_norm == "all":
            return RelayResult(relay_state=relay.get_state())

        return RelayResult(relay_state=relay.get_relay_state(relay_number_norm))

    @staticmethod
    def get_devices() -> List[Dict[str, str]]:
        return enumerate_devices() or []
