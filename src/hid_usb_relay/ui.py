"""Dear PyGui desktop UI for HID USB Relay control."""

import dearpygui.dearpygui as dpg

from hid_usb_relay.service import RelayService
from hid_usb_relay.usb_relay import RelayError

service = RelayService()


def _set_status(text: str, color=(200, 220, 255, 255)) -> None:
    dpg.set_value("status_text", text)
    dpg.configure_item("status_text", color=color)


def _selected_device() -> str | None:
    val = dpg.get_value("device_combo")
    return None if val == "Default" else val


def _scan_devices() -> None:
    try:
        devices = service.get_devices()
        ids = ["Default"] + [d["device_id"] for d in devices if d.get("device_id")]
        dpg.configure_item("device_combo", items=ids)
        if ids:
            dpg.set_value("device_combo", ids[0])

        dpg.delete_item("device_table", children_only=True, slot=1)
        for dev in devices:
            with dpg.table_row(parent="device_table"):
                dpg.add_text(dev.get("device_id", "Unknown"))
                relay_states = [f"{k}={v}" for k, v in dev.items() if k.startswith("R")]
                dpg.add_text("  ".join(relay_states))
        _set_status(f"Discovered {len(devices)} devices", (120, 255, 170, 255))
    except Exception as exc:
        _set_status(f"Scan failed: {exc}", (255, 120, 120, 255))


def _control(state: str) -> None:
    relay_number = dpg.get_value("relay_input").strip().lower()
    relay_id = _selected_device()
    try:
        result = service.set_and_get_relay_state(relay_id, relay_number, state)
        _set_status(f"{relay_id or 'Default'} relay {relay_number} => {state.upper()}", (120, 255, 170, 255))
        dpg.set_value("output_text", str(result.relay_state))
    except RelayError as exc:
        _set_status(str(exc), (255, 120, 120, 255))


def run_gui() -> None:
    dpg.create_context()

    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 8)
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (18, 22, 38, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (30, 35, 58, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Button, (91, 84, 255, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (119, 113, 255, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (38, 45, 75, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Header, (0, 191, 166, 190))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (22, 163, 74, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (235, 241, 255, 255))

    dpg.bind_theme(global_theme)

    with dpg.window(label="HID USB Relay • Control Center", width=980, height=700):
        dpg.add_text("Modern Desktop Relay Controller", color=(0, 230, 200, 255))
        dpg.add_separator()

        with dpg.group(horizontal=True):
            dpg.add_text("Device")
            dpg.add_combo(["Default"], default_value="Default", width=220, tag="device_combo")
            dpg.add_button(label="Scan Devices", callback=lambda: _scan_devices())

        with dpg.group(horizontal=True):
            dpg.add_text("Relay")
            dpg.add_input_text(default_value="all", width=120, tag="relay_input")
            dpg.add_button(label="TURN ON", callback=lambda: _control("on"))
            dpg.add_button(label="TURN OFF", callback=lambda: _control("off"))

        dpg.add_spacer(height=8)
        dpg.add_text("status", tag="status_text", color=(180, 200, 255, 255))
        dpg.add_input_text(tag="output_text", multiline=True, readonly=True, width=-1, height=120)

        dpg.add_spacer(height=8)
        dpg.add_text("Discovered Devices", color=(255, 215, 120, 255))
        with dpg.table(header_row=True, resizable=True, borders_innerH=True, borders_outerH=True, borders_innerV=True,
                       borders_outerV=True, row_background=True, tag="device_table"):
            dpg.add_table_column(label="Device ID", width_stretch=True)
            dpg.add_table_column(label="Relay States", width_stretch=True)

    dpg.create_viewport(title="HID USB Relay", width=1000, height=760)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    _scan_devices()
    dpg.start_dearpygui()
    dpg.destroy_context()
