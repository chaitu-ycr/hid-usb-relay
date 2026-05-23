import argparse
import json
import sys
from typing import Sequence, Optional

from hid_usb_relay.usb_relay import RelayError, RelayService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='hid-usb-relay', description='Control HID USB relay devices from the command line.')
    subparsers = parser.add_subparsers(dest='command', required=True)
    subparsers.add_parser('devices', help='List connected relay devices.')
    state_parser = subparsers.add_parser('state', aliases=['status'], help='Read relay state.')
    state_parser.add_argument('relay_number', help='Relay number (1-8) or all.')
    state_parser.add_argument('--relay-id', dest='relay_id', help='Optional relay device ID.')
    control_parser = subparsers.add_parser('control', help='Set relay state.')
    control_parser.add_argument('relay_number', help='Relay number (1-8) or all.')
    control_parser.add_argument('relay_state', choices=['on', 'off'], help='Relay state.')
    control_parser.add_argument('--relay-id', dest='relay_id', help='Optional relay device ID.')
    return parser


def _print_json(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def run_cli(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    service = RelayService()
    try:
        if args.command == 'devices':
            devices = service.get_devices()
            _print_json({'devices': devices, 'count': len(devices)})
            return 0
        if args.command in ('state', 'status'):
            result = service.get_state(args.relay_id, args.relay_number)
        else:
            result = service.set_and_get_relay_state(args.relay_id, args.relay_number, args.relay_state)
        _print_json({'relay_number': args.relay_number, 'relay_id': args.relay_id, 'relay_state': result.relay_state})
        return 0
    except RelayError as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(run_cli())
