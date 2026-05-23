from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence, Optional

from hid_usb_relay.usb_relay import RelayError, RelayService


__all__ = ["HIDUSBRelayCLI", "run_cli"]

class HIDUSBRelayCLI:
    def __init__(self) -> None:
        self.service = RelayService()

    @staticmethod
    def _print_json(value: object) -> None:
        print(json.dumps(value, indent=2, ensure_ascii=False))

    def parse_args(self, argv: Sequence[str] | None = None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            prog="hid-usb-relay",
            description="Control HID USB relay devices from the command line.",
        )
        subparsers = parser.add_subparsers(dest="command", required=True)

        subparsers.add_parser("devices", help="List connected relay devices.")

        state_parser = subparsers.add_parser("state", aliases=["status"], help="Read relay state.")
        state_parser.add_argument(
            "relay_number",
            help="Relay number (1-8) or all.",
        )
        state_parser.add_argument(
            "--relay-id",
            dest="relay_id",
            help="Optional relay device ID.",
        )

        control_parser = subparsers.add_parser("control", help="Set relay state.")
        control_parser.add_argument(
            "relay_number",
            help="Relay number (1-8) or all.",
        )
        control_parser.add_argument(
            "relay_state",
            choices=["on", "off"],
            help="Relay state.",
        )
        control_parser.add_argument(
            "--relay-id",
            dest="relay_id",
            help="Optional relay device ID.",
        )

        return parser.parse_args(argv)

    def list_devices(self) -> int:
        devices = self.service.get_devices()
        self._print_json({"devices": devices, "count": len(devices)})
        return 0

    def read_state(self, relay_number: str, relay_id: Optional[str] = None) -> int:
        result = self.service.get_state(relay_id, relay_number)
        self._print_json({"relay_number": relay_number, "relay_id": relay_id, "relay_state": result.relay_state})
        return 0

    def control_relay(self, relay_number: str, relay_state: str, relay_id: Optional[str] = None) -> int:
        result = self.service.set_and_get_relay_state(relay_id, relay_number, relay_state)
        self._print_json({"relay_number": relay_number, "relay_id": relay_id, "relay_state": result.relay_state})
        return 0

    def run(self, argv: Sequence[str] | None = None) -> int:
        args = self.parse_args(argv)
        try:
            if args.command == "devices":
                return self.list_devices()
            if args.command in ("state", "status"):
                return self.read_state(args.relay_number, args.relay_id)
            if args.command == "control":
                return self.control_relay(args.relay_number, args.relay_state, args.relay_id)

            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1
        except RelayError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1


def run_cli(argv: Sequence[str] | None = None) -> int:
    return HIDUSBRelayCLI().run(argv)


if __name__ == "__main__":
    raise SystemExit(run_cli())
