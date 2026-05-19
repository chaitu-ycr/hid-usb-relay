"""Application entrypoints for API server and Dear PyGui desktop UI."""

from argparse import ArgumentParser
import re

from fastapi import FastAPI, Request
import uvicorn

from hid_usb_relay.api import router, root_router
from hid_usb_relay.ui import run_gui


def create_api_app() -> FastAPI:
    app = FastAPI(title="HID USB Relay API", version="1.0.0")

    @app.middleware("http")
    async def normalize_path(request: Request, call_next):
        path = request.scope.get("path", "")
        normalized = re.sub(r"/{2,}", "/", path)
        if normalized != path:
            request.scope["path"] = normalized
            request.scope["raw_path"] = normalized.encode("utf-8")
        return await call_next(request)

    app.include_router(router)
    app.include_router(root_router)
    return app


def run_gui_mode() -> None:
    """Run application in GUI mode."""
    run_gui()


def run_api_mode() -> None:
    """Run application in API mode."""
    parser = ArgumentParser(description="HID USB Relay API")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=9400, help="Port number")
    args = parser.parse_args()
    uvicorn.run(create_api_app(), host=args.host, port=args.port)


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
