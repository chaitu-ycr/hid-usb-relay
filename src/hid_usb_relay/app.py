"""Application entrypoints for API server and Dear PyGui desktop UI."""

from argparse import ArgumentParser

from fastapi import FastAPI
import uvicorn

from hid_usb_relay.api import router
from hid_usb_relay.ui import run_gui


def create_api_app() -> FastAPI:
    app = FastAPI(title="HID USB Relay API", version="1.0.0")
    app.include_router(router)
    return app


def main() -> None:
    parser = ArgumentParser(description="HID USB Relay")
    parser.add_argument("--mode", choices=["api", "gui"], default="gui")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=9400, help="Port number")
    args = parser.parse_args()

    if args.mode == "api":
        uvicorn.run(create_api_app(), host=args.host, port=args.port)
    else:
        run_gui()


if __name__ == "__main__":
    main()
