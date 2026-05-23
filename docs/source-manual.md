# Source Manual

This manual provides a quick overview of the `hid_usb_relay` package and links to each documented interface.

## Documentation pages

- [USB Relay](usb_relay.md) — low-level relay control classes and helpers
- [API](api.md) — FastAPI server interface and HTTP endpoints
- [CLI](cli.md) — command-line relay control interface
- [GUI](gui.md) — desktop graphical user interface

## Overview

The package supports three independent user interfaces while sharing a single relay control implementation in `hid_usb_relay.usb_relay`.

- `hid_usb_relay.usb_relay` contains the core device and service classes.
- `hid_usb_relay.api` exposes HTTP endpoints via FastAPI.
- `hid_usb_relay.cli` provides a command-line experience.
- `hid_usb_relay.gui` launches a Dear PyGui desktop app.



