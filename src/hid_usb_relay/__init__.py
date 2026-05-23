"""Package entrypoint for hid_usb_relay."""

from hid_usb_relay.api import app, run_api
from hid_usb_relay.cli import run_cli
from hid_usb_relay.gui import HIDUSBRelayGUI, run_gui
from hid_usb_relay.usb_relay import (
    USBRelayDevice,
    RelayState,
    RelayError,
    RelayCommandError,
    RelayValidationError,
    RelayService,
    enumerate_devices,
    get_platform_info,
    get_bin_directory,
    get_executable_path,
)

__all__ = [
    "app",
    "run_api",
    "run_cli",
    "HIDUSBRelayGUI",
    "run_gui",
    "USBRelayDevice",
    "RelayState",
    "RelayError",
    "RelayCommandError",
    "RelayValidationError",
    "RelayService",
    "enumerate_devices",
    "get_platform_info",
    "get_bin_directory",
    "get_executable_path",
]
