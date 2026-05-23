"""
HID USB Relay Controller Module

Provides an object-oriented interface for controlling HID USB relay devices
via command-line executable. Supports multiple relay devices with proper
error handling, validation, and reusability.

Example:
    >>> relay = USBRelayDevice()  # Default device
    >>> relay.turn_on(1)
    >>> relay.get_state()
    {'R1': 'ON', 'R2': 'OFF'}

    >>> specific = USBRelayDevice(device_id='HURTM')
    >>> specific.turn_on_all()

    >>> # Context manager pattern
    >>> with USBRelayDevice('HURTM') as relay:
    ...     relay.turn_on_all()
"""

import logging
import platform
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

__all__ = [
    "USBRelayDevice",
    "enumerate_devices",
    "RelayState",
    "RelayError",
    "RelayCommandError",
    "RelayValidationError",
    "RelayService",
]


class RelayState(Enum):
    """Relay state enumeration."""

    ON = "on"
    OFF = "off"


class RelayCommand(Enum):
    """Available relay commands."""

    STATE = "state"
    ENUM = "enum"


class RelayError(Exception):
    """Base exception for relay operations."""


class RelayCommandError(RelayError):
    """Raised when relay command execution fails."""


class RelayValidationError(RelayError):
    """Raised when input validation fails."""


@dataclass(frozen=True)
class PlatformInfo:
    """Platform and architecture information."""

    system: str
    architecture: str

    @property
    def is_windows(self) -> bool:
        return self.system == "windows"

    @property
    def is_linux(self) -> bool:
        return self.system == "linux"

    @property
    def arch_bits(self) -> str:
        """Get architecture as bit string (32bit/64bit)."""
        return "64bit" if "64" in self.architecture else "32bit"


class HIDUSBRelayModule:
    """Encapsulates USB relay command logic."""

    DEFAULT_TIMEOUT = 5.0
    MAX_RELAY_COUNT = 8
    logger = logging.getLogger(__name__)

    @classmethod
    def get_platform_info(cls) -> PlatformInfo:
        return PlatformInfo(
            system=platform.system().lower(),
            architecture=platform.architecture()[0].lower(),
        )

    @classmethod
    def _get_module_bin_directory(cls) -> Path:
        return Path(__file__).parent / "hid_usb_relay_bin"

    @classmethod
    def get_bin_directory(cls, base_path: Optional[Union[str, Path]] = None) -> Path:
        if base_path is None:
            return cls._get_module_bin_directory()
        return Path(base_path) / "hid_usb_relay_bin"

    @classmethod
    def _get_default_executable_path(cls) -> Path:
        plat = cls.get_platform_info()

        if not (plat.is_windows or plat.is_linux):
            raise RelayError(f"Unsupported platform: {plat.system}")

        bin_dir = cls._get_module_bin_directory()
        exe_name = "hidusb-relay-cmd.exe" if plat.is_windows else "hidusb-relay-cmd"
        exe_path = bin_dir / plat.system / plat.arch_bits / exe_name

        if not exe_path.exists():
            raise RelayError(f"Executable not found: {exe_path}")

        return exe_path

    @classmethod
    def get_executable_path(cls, base_path: Optional[Union[str, Path]] = None) -> Path:
        if base_path is None:
            return cls._get_default_executable_path()

        plat = cls.get_platform_info()

        if not (plat.is_windows or plat.is_linux):
            raise RelayError(f"Unsupported platform: {plat.system}")

        bin_dir = cls.get_bin_directory(base_path)
        exe_name = "hidusb-relay-cmd.exe" if plat.is_windows else "hidusb-relay-cmd"
        exe_path = bin_dir / plat.system / plat.arch_bits / exe_name

        if not exe_path.exists():
            raise RelayError(f"Executable not found: {exe_path}")

        return exe_path

    @classmethod
    def _execute_command(cls, command: List[Union[Path, str]], timeout: float = DEFAULT_TIMEOUT) -> str:
        cmd_str = [str(c) for c in command]
        cls.logger.debug(f"Executing: {' '.join(cmd_str)}")

        try:
            result = subprocess.run(
                cmd_str,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=timeout,
            )
            output = result.stdout.strip() if result.stdout else ""
            if output:
                cls.logger.debug(f"Output: {output}")
            return output

        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed (exit {e.returncode}): {e.stderr.strip() if e.stderr else 'Unknown error'}"
            cls.logger.error(error_msg)
            raise RelayCommandError(error_msg) from e
        except subprocess.TimeoutExpired as e:
            error_msg = f"Command timed out after {timeout}s"
            cls.logger.error(error_msg)
            raise RelayCommandError(error_msg) from e
        except FileNotFoundError as e:
            error_msg = f"Executable not found: {command[0]}"
            cls.logger.error(error_msg)
            raise RelayCommandError(error_msg) from e
        except OSError as e:
            error_msg = f"OS error executing command: {e}"
            cls.logger.error(error_msg)
            raise RelayCommandError(error_msg) from e

    @staticmethod
    def _parse_relay_states(output: str) -> Dict[str, str]:
        if not output or "State:" not in output:
            raise RelayError(f"Invalid state format: {output}")

        state_str = output.split("State:", 1)[-1].strip()
        pattern = re.compile(r"(R\d+)=(ON|OFF)", re.IGNORECASE)
        matches = pattern.findall(state_str)

        if not matches:
            raise RelayError(f"No relay states found in: {output}")

        return {relay: state.upper() for relay, state in matches}

    @classmethod
    def _validate_relay_number(cls, relay_num: Union[int, str], max_relays: Optional[int] = None) -> int:
        if max_relays is None:
            max_relays = cls.MAX_RELAY_COUNT

        try:
            num = int(relay_num)
        except (ValueError, TypeError) as exc:
            raise RelayValidationError(f"Invalid relay number format: {relay_num!r}") from exc

        if not 1 <= num <= max_relays:
            raise RelayValidationError(
                f"Relay number must be between 1 and {max_relays}, got {num}"
            )

        return num

    @classmethod
    def enumerate_devices(cls) -> List[Dict[str, str]]:
        exe_path = cls._get_default_executable_path()
        output = cls._execute_command([exe_path, RelayCommand.ENUM.value])
        device_pattern = re.compile(r"Board ID=\[([^\]]+)\]", re.IGNORECASE)

        devices: List[Dict[str, str]] = []
        for line in output.split("\n"):
            if not line.strip():
                continue

            match = device_pattern.search(line)
            if match:
                device_id = match.group(1)
                try:
                    states = cls._parse_relay_states(line)
                    devices.append({"device_id": device_id, **states})
                except RelayError as exc:
                    cls.logger.warning(f"Failed to parse device {device_id}: {exc}")

        cls.logger.info(f"Found {len(devices)} relay device(s)")
        return devices


@dataclass(frozen=True)
class RelayResult:
    relay_state: Union[str, Dict[str, str]]


class USBRelayDevice:
    """Interface for controlling a USB relay device."""

    def __init__(
        self,
        device_id: Optional[str] = None,
        executable_path: Optional[Union[str, Path]] = None,
        timeout: Optional[float] = None,
    ):
        self.device_id = device_id
        self._timeout = timeout if timeout is not None else HIDUSBRelayModule.DEFAULT_TIMEOUT
        self._exe_path = Path(executable_path) if executable_path else HIDUSBRelayModule.get_executable_path()
        HIDUSBRelayModule.logger.info(f"Initialized USB relay: {device_id or 'default'}")

    def __enter__(self) -> "USBRelayDevice":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def __repr__(self) -> str:
        return f"USBRelayDevice(device_id={self.device_id!r})"

    def _build_command(self, action: str, target: Optional[str] = None) -> List[Union[Path, str]]:
        cmd: List[Union[Path, str]] = [self._exe_path]
        if self.device_id:
            cmd.append(f"id={self.device_id}")
        cmd.append(action)
        if target is not None:
            cmd.append(target)
        return cmd

    def _execute(self, action: str, target: Optional[str] = None) -> str:
        return HIDUSBRelayModule._execute_command(self._build_command(action, target), timeout=self._timeout)

    def get_state(self) -> Dict[str, str]:
        output = self._execute(RelayCommand.STATE.value)
        return HIDUSBRelayModule._parse_relay_states(output)

    def get_relay_state(self, relay_num: Union[int, str]) -> str:
        num = HIDUSBRelayModule._validate_relay_number(relay_num)
        states = self.get_state()
        relay_key = f"R{num}"
        if relay_key not in states:
            raise RelayError(
                f"Relay {num} not found. Available: {', '.join(states.keys())}"
            )
        return states[relay_key]

    def set_state(
        self,
        state: Union[RelayState, str],
        relay_num: Optional[Union[int, str]] = None,
    ) -> None:
        if isinstance(state, RelayState):
            state_str = state.value
        elif isinstance(state, str):
            state_str = state.lower()
            if state_str not in ("on", "off"):
                raise RelayValidationError(
                    f"Invalid state: {state!r}. Must be 'on' or 'off'"
                )
        else:
            raise RelayValidationError(
                f"State must be RelayState or str, got {type(state).__name__}"
            )

        if relay_num is None:
            target = "all"
        else:
            target = str(HIDUSBRelayModule._validate_relay_number(relay_num))

        self._execute(state_str, target)
        HIDUSBRelayModule.logger.info(
            f"Set {self.device_id or 'default'} relay {target} to {state_str.upper()}"
        )

    def turn_on(self, relay_num: Union[int, str]) -> None:
        self.set_state(RelayState.ON, relay_num)

    def turn_off(self, relay_num: Union[int, str]) -> None:
        self.set_state(RelayState.OFF, relay_num)

    def turn_on_all(self) -> None:
        self.set_state(RelayState.ON)

    def turn_off_all(self) -> None:
        self.set_state(RelayState.OFF)


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
        return HIDUSBRelayModule.enumerate_devices() or []


enumerate_devices = HIDUSBRelayModule.enumerate_devices
