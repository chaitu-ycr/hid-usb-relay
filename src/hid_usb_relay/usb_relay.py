"""Core domain and process layer for HID USB relay control.

This module provides a small object model around the vendor CLI binary and
normalizes command execution, relay validation, and output parsing.
"""

from __future__ import annotations

import logging
import platform
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

__all__ = [
    'USBRelayDevice',
    'enumerate_devices',
    'RelayState',
    'RelayError',
    'RelayCommandError',
    'RelayValidationError',
    'RelayService',
    'RelayResult',
    'get_platform_info',
    'get_bin_directory',
    'get_executable_path',
]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RelayConfig:
    """Shared runtime constants for relay interactions."""

    default_timeout: float = 5.0
    max_relay_count: int = 8
    relay_cmd: Dict[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'relay_cmd', self.relay_cmd or {'windows': 'hidusb-relay-cmd.exe', 'linux': 'hidusb-relay-cmd'})


CONFIG = RelayConfig()


class RelayState(Enum):
    """Supported relay state transitions."""

    ON = 'on'
    OFF = 'off'


class RelayCommand(Enum):
    """CLI actions exposed by the vendor executable."""

    STATE = 'state'
    ENUM = 'enum'


class RelayError(Exception):
    """Base relay exception."""


class RelayCommandError(RelayError):
    """Raised when command execution fails."""


class RelayValidationError(RelayError):
    """Raised when relay input values are invalid."""


class RelayRuntime:
    """Encapsulates executable discovery and subprocess execution."""

    def __init__(self, base_path: Optional[Union[str, Path]] = None, timeout: float = CONFIG.default_timeout) -> None:
        self.base_path = Path(base_path) if base_path else Path(__file__).parent
        self.timeout = timeout

    @property
    def bin_directory(self) -> Path:
        return self.base_path / 'hid_usb_relay_bin'

    @property
    def platform_info(self) -> Dict[str, str]:
        system = platform.system().lower()
        if system not in CONFIG.relay_cmd:
            raise RelayError(f'Unsupported platform: {system}')
        return {'system': system, 'architecture': platform.architecture()[0].lower()}

    @property
    def executable_path(self) -> Path:
        info = self.platform_info
        bitness = '64bit' if '64' in info['architecture'] else '32bit'
        executable = self.bin_directory / info['system'] / bitness / CONFIG.relay_cmd[info['system']]
        if not executable.exists():
            raise RelayError(f'Executable not found: {executable}')
        return executable

    def run(self, command: List[Union[Path, str]]) -> str:
        try:
            result = subprocess.run(
                [str(item) for item in command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=self.timeout,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as exc:
            raise RelayCommandError(f'Command failed (exit {exc.returncode}): {exc.stderr.strip() or "Unknown error"}') from exc
        except subprocess.TimeoutExpired as exc:
            raise RelayCommandError(f'Command timed out after {self.timeout}s') from exc
        except (FileNotFoundError, OSError) as exc:
            raise RelayCommandError(f'Execution error: {exc}') from exc


RUNTIME = RelayRuntime()


def get_bin_directory(base_path: Optional[Union[str, Path]] = None) -> Path:
    """Return the binary directory for a given package base path."""

    return RelayRuntime(base_path=base_path).bin_directory


def get_executable_path(base_path: Optional[Union[str, Path]] = None) -> Path:
    """Return the platform-specific relay executable path."""

    return RelayRuntime(base_path=base_path).executable_path


def get_platform_info() -> Dict[str, str]:
    """Return normalized host platform metadata."""

    return RUNTIME.platform_info


def _parse_relay_states(output: str) -> Dict[str, str]:
    matches = re.findall(r'(R\d+)=(ON|OFF)', output or '', re.IGNORECASE)
    if not matches:
        raise RelayError(f'Invalid state format: {output}')
    return {relay: state.upper() for relay, state in matches}


def _validate_relay_number(relay_num: Union[int, str]) -> int:
    try:
        relay = int(relay_num)
    except (TypeError, ValueError) as exc:
        raise RelayValidationError(f'Invalid relay number format: {relay_num!r}') from exc
    if not 1 <= relay <= CONFIG.max_relay_count:
        raise RelayValidationError(f'Relay number must be between 1 and {CONFIG.max_relay_count}, got {relay}')
    return relay


def enumerate_devices() -> List[Dict[str, str]]:
    """Enumerate connected relay devices and their current states."""

    output = RUNTIME.run([RUNTIME.executable_path, RelayCommand.ENUM.value])
    devices: List[Dict[str, str]] = []
    for line in output.splitlines():
        board = re.search(r'Board ID=\[([^\]]+)\]', line, re.IGNORECASE)
        if not board:
            continue
        try:
            devices.append({'device_id': board.group(1), **_parse_relay_states(line)})
        except RelayError as exc:
            logger.warning('%s', exc)
    return devices


@dataclass(frozen=True)
class RelayResult:
    """Service return payload for relay operations."""

    relay_state: Union[str, Dict[str, str]]


class USBRelayDevice:
    """Device wrapper used for state reads and writes."""

    def __init__(self, device_id: Optional[str] = None, runtime: RelayRuntime = RUNTIME) -> None:
        self.device_id = device_id
        self.runtime = runtime

    def _execute(self, action: str, target: Optional[str] = None) -> str:
        command: List[Union[Path, str]] = [self.runtime.executable_path]
        if self.device_id:
            command.append(f'id={self.device_id}')
        command.append(action)
        if target is not None:
            command.append(target)
        return self.runtime.run(command)

    def get_state(self) -> Dict[str, str]:
        return _parse_relay_states(self._execute(RelayCommand.STATE.value))

    def get_relay_state(self, relay_num: Union[int, str]) -> str:
        key = f'R{_validate_relay_number(relay_num)}'
        state_map = self.get_state()
        if key not in state_map:
            raise RelayError(f"Relay {key} not found. Available: {', '.join(state_map)}")
        return state_map[key]

    def set_state(self, state: Union[RelayState, str], relay_num: Optional[Union[int, str]] = None) -> None:
        value = state.value if isinstance(state, RelayState) else state.strip().lower()
        if value not in ('on', 'off'):
            raise RelayValidationError(f'Invalid state: {state!r}. Must be "on" or "off"')
        self._execute(value, 'all' if relay_num is None else str(_validate_relay_number(relay_num)))


class RelayService:
    """Application service used by API/CLI/GUI layers."""

    def _device(self, relay_id: Optional[str]) -> USBRelayDevice:
        return USBRelayDevice(device_id=relay_id)

    def set_and_get_relay_state(self, relay_id: Optional[str], relay_number: str, state: str) -> RelayResult:
        relay = self._device(relay_id)
        relay_number = relay_number.strip().lower()
        relay.set_state(state, None if relay_number == 'all' else relay_number)
        return RelayResult(relay_state=relay.get_state() if relay_number == 'all' else relay.get_relay_state(relay_number))

    def get_state(self, relay_id: Optional[str], relay_number: str) -> RelayResult:
        relay = self._device(relay_id)
        relay_number = relay_number.strip().lower()
        return RelayResult(relay_state=relay.get_state() if relay_number == 'all' else relay.get_relay_state(relay_number))

    def get_devices(self) -> List[Dict[str, str]]:
        return enumerate_devices()
