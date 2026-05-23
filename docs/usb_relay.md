# USB Relay Module

This page documents the low-level relay control module in `hid_usb_relay`.

The module provides:

- `RelayRuntime` — executable discovery and command execution
- `USBRelayDevice` — control a specific relay device
- `RelayService` — service layer for relay operations
- `enumerate_devices()` — list connected HID USB relay boards
- `RelayState`, `RelayError`, and validation helpers

::: hid_usb_relay.usb_relay
