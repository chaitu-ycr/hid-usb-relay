"""Public package exports for hid_usb_relay."""

from hid_usb_relay.api import app, run_api
from hid_usb_relay.gui import HIDUSBRelayGUI, run_gui
from hid_usb_relay.usb_relay import (
    RelayCommandError,
    RelayError,
    RelayService,
    RelayState,
    RelayValidationError,
    USBRelayDevice,
    enumerate_devices,
    get_bin_directory,
    get_executable_path,
    get_platform_info,
)


def run_cli(argv=None):
    """Lazy CLI entrypoint to avoid premature cli module import side effects."""

    from hid_usb_relay.cli import run_cli as _run_cli

    return _run_cli(argv)


__all__ = [
    'app',
    'run_api',
    'run_cli',
    'HIDUSBRelayGUI',
    'run_gui',
    'USBRelayDevice',
    'RelayState',
    'RelayError',
    'RelayCommandError',
    'RelayValidationError',
    'RelayService',
    'enumerate_devices',
    'get_platform_info',
    'get_bin_directory',
    'get_executable_path',
]
