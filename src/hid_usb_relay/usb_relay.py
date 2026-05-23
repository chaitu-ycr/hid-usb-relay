import logging
import platform
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

__all__ = [
    'USBRelayDevice', 'enumerate_devices', 'RelayState', 'RelayError',
    'RelayCommandError', 'RelayValidationError', 'RelayService',
    'get_platform_info', 'get_bin_directory', 'get_executable_path',
]

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 5.0
MAX_RELAY_COUNT = 8
RELAY_CMD = {'windows': 'hidusb-relay-cmd.exe', 'linux': 'hidusb-relay-cmd'}

class RelayState(Enum):
    ON = 'on'
    OFF = 'off'

class RelayCommand(Enum):
    STATE = 'state'
    ENUM = 'enum'

class RelayError(Exception):
    pass

class RelayCommandError(RelayError):
    pass

class RelayValidationError(RelayError):
    pass


def _platform_info() -> tuple[str, str]:
    sys_name = platform.system().lower()
    if sys_name not in RELAY_CMD:
        raise RelayError(f'Unsupported platform: {sys_name}')
    return sys_name, platform.architecture()[0].lower()


def _bin_dir(base_path: Optional[Union[str, Path]] = None) -> Path:
    base = Path(base_path) if base_path else Path(__file__).parent
    return base / 'hid_usb_relay_bin'


def get_bin_directory(base_path: Optional[Union[str, Path]] = None) -> Path:
    return _bin_dir(base_path)


def _executable_name(sys_name: str) -> str:
    return RELAY_CMD[sys_name]


def get_executable_path(base_path: Optional[Union[str, Path]] = None) -> Path:
    sys_name, arch = _platform_info()
    exe = _bin_dir(base_path) / sys_name / ('64bit' if '64' in arch else '32bit') / _executable_name(sys_name)
    if not exe.exists():
        raise RelayError(f'Executable not found: {exe}')
    return exe


def get_platform_info() -> Dict[str, str]:
    sys_name, arch = _platform_info()
    return {'system': sys_name, 'architecture': arch}


def _run(command: List[Union[Path, str]], timeout: float = DEFAULT_TIMEOUT) -> str:
    try:
        result = subprocess.run(
            [str(item) for item in command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise RelayCommandError(f'Command failed (exit {exc.returncode}): {exc.stderr.strip() or "Unknown error"}') from exc
    except subprocess.TimeoutExpired as exc:
        raise RelayCommandError(f'Command timed out after {timeout}s') from exc
    except FileNotFoundError as exc:
        raise RelayCommandError(f'Executable not found: {command[0]}') from exc
    except OSError as exc:
        raise RelayCommandError(f'OS error executing command: {exc}') from exc


def _parse_relay_states(output: str) -> Dict[str, str]:
    matches = re.findall(r'(R\d+)=(ON|OFF)', output or '', re.IGNORECASE)
    if not matches:
        raise RelayError(f'Invalid state format: {output}')
    return {key: value.upper() for key, value in matches}


def _validate_relay_number(relay_num: Union[int, str]) -> int:
    try:
        relay = int(relay_num)
    except (TypeError, ValueError) as exc:
        raise RelayValidationError(f'Invalid relay number format: {relay_num!r}') from exc
    if not 1 <= relay <= MAX_RELAY_COUNT:
        raise RelayValidationError(f'Relay number must be between 1 and {MAX_RELAY_COUNT}, got {relay}')
    return relay


def enumerate_devices() -> List[Dict[str, str]]:
    output = _run([get_executable_path(), RelayCommand.ENUM.value])
    devices: List[Dict[str, str]] = []
    for line in output.splitlines():
        match = re.search(r'Board ID=\[([^\]]+)\]', line, re.IGNORECASE)
        if not match:
            continue
        try:
            devices.append({'device_id': match.group(1), **_parse_relay_states(line)})
        except RelayError as exc:
            logger.warning('%s', exc)
    return devices


@dataclass(frozen=True)
class RelayResult:
    relay_state: Union[str, Dict[str, str]]


class USBRelayDevice:
    def __init__(
        self,
        device_id: Optional[str] = None,
        executable_path: Optional[Union[str, Path]] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.device_id = device_id
        self._timeout = timeout
        self._exe_path = Path(executable_path) if executable_path else get_executable_path()

    def __enter__(self) -> 'USBRelayDevice':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def _build_command(self, action: str, target: Optional[str] = None) -> List[Union[Path, str]]:
        cmd: List[Union[Path, str]] = [self._exe_path]
        if self.device_id:
            cmd.append(f'id={self.device_id}')
        cmd.append(action)
        if target is not None:
            cmd.append(target)
        return cmd

    def _execute(self, action: str, target: Optional[str] = None) -> str:
        return _run(self._build_command(action, target), timeout=self._timeout)

    def get_state(self) -> Dict[str, str]:
        return _parse_relay_states(self._execute(RelayCommand.STATE.value))

    def get_relay_state(self, relay_num: Union[int, str]) -> str:
        key = f'R{_validate_relay_number(relay_num)}'
        states = self.get_state()
        if key not in states:
            raise RelayError(f"Relay {key} not found. Available: {', '.join(states)}")
        return states[key]

    def set_state(self, state: Union[RelayState, str], relay_num: Optional[Union[int, str]] = None) -> None:
        value = state.value if isinstance(state, RelayState) else state.lower()
        if value not in ('on', 'off'):
            raise RelayValidationError(f'Invalid state: {state!r}. Must be "on" or "off"')
        target = 'all' if relay_num is None else str(_validate_relay_number(relay_num))
        self._execute(value, target)

    def turn_on(self, relay_num: Union[int, str]) -> None:
        self.set_state(RelayState.ON, relay_num)

    def turn_off(self, relay_num: Union[int, str]) -> None:
        self.set_state(RelayState.OFF, relay_num)

    def turn_on_all(self) -> None:
        self.set_state(RelayState.ON)

    def turn_off_all(self) -> None:
        self.set_state(RelayState.OFF)


class RelayService:
    @staticmethod
    def set_and_get_relay_state(relay_id: Optional[str], relay_number: str, state: str) -> RelayResult:
        relay = USBRelayDevice(device_id=relay_id)
        relay_number_norm = relay_number.strip().lower()
        state_norm = state.strip().lower()
        if relay_number_norm == 'all':
            relay.set_state(state_norm)
            return RelayResult(relay_state=relay.get_state())
        relay.set_state(state_norm, relay_number_norm)
        return RelayResult(relay_state=relay.get_relay_state(relay_number_norm))

    @staticmethod
    def get_state(relay_id: Optional[str], relay_number: str) -> RelayResult:
        relay = USBRelayDevice(device_id=relay_id)
        relay_number_norm = relay_number.strip().lower()
        if relay_number_norm == 'all':
            return RelayResult(relay_state=relay.get_state())
        return RelayResult(relay_state=relay.get_relay_state(relay_number_norm))

    @staticmethod
    def get_devices() -> List[Dict[str, str]]:
        return enumerate_devices()
