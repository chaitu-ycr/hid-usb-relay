"""Command-line interface for HID USB relay operations."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from hid_usb_relay.usb_relay import RelayError, RelayService


class RelayCLI:
    """CLI application wrapper that owns parser and service usage."""

    def __init__(self) -> None:
        self.service = RelayService()

    @staticmethod
    def _parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog='hid-usb-relay',
            description='Control HID USB relay devices from the command line.',
        )
        subparsers = parser.add_subparsers(dest='command', required=True)

        subparsers.add_parser('devices', help='List connected relay devices.')

        state = subparsers.add_parser('state', aliases=['status'], help='Read relay state.')
        control = subparsers.add_parser('control', help='Set relay state.')
        for sub in (state, control):
            sub.add_argument('relay_number', help='Relay number (1-8) or all.')
            sub.add_argument('--relay-id', dest='relay_id', help='Optional relay device ID.')

        control.add_argument('relay_state', choices=['on', 'off'], help='Relay state.')
        return parser

    @staticmethod
    def _print_json(payload: object) -> None:
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    def _run_devices(self) -> None:
        devices = self.service.get_devices()
        self._print_json({'devices': devices, 'count': len(devices)})

    def _run_state(self, relay_id: str | None, relay_number: str) -> None:
        result = self.service.get_state(relay_id, relay_number)
        self._print_json({'relay_number': relay_number, 'relay_id': relay_id, 'relay_state': result.relay_state})

    def _run_control(self, relay_id: str | None, relay_number: str, relay_state: str) -> None:
        result = self.service.set_and_get_relay_state(relay_id, relay_number, relay_state)
        self._print_json({'relay_number': relay_number, 'relay_id': relay_id, 'relay_state': result.relay_state})

    def run(self, argv: Sequence[str] | None = None) -> int:
        args = self._parser().parse_args(argv)
        try:
            if args.command == 'devices':
                self._run_devices()
            elif args.command in ('state', 'status'):
                self._run_state(args.relay_id, args.relay_number)
            else:
                self._run_control(args.relay_id, args.relay_number, args.relay_state)
            return 0
        except RelayError as exc:
            print(f'Error: {exc}', file=sys.stderr)
            return 1


def run_cli(argv: Sequence[str] | None = None) -> int:
    """Entrypoint compatible wrapper for packaging scripts."""

    return RelayCLI().run(argv)


if __name__ == '__main__':
    raise SystemExit(run_cli())
