"""DearPyGui-based desktop GUI for HID USB relay control."""

from typing import Any

from hid_usb_relay.usb_relay import RelayError, RelayService

__all__ = ['HIDUSBRelayGUI', 'run_gui']


class HIDUSBRelayGUI:
    """GUI application that owns widgets, theme, and relay operations."""

    THEME_STYLES = [('mvStyleVar_WindowRounding', 10), ('mvStyleVar_FrameRounding', 8), ('mvStyleVar_ItemSpacing', 10, 8)]
    THEME_COLORS = [
        ('mvThemeCol_WindowBg', (18, 22, 38, 255)), ('mvThemeCol_ChildBg', (30, 35, 58, 255)),
        ('mvThemeCol_Button', (91, 84, 255, 255)), ('mvThemeCol_ButtonHovered', (119, 113, 255, 255)),
        ('mvThemeCol_FrameBg', (38, 45, 75, 255)), ('mvThemeCol_Header', (0, 191, 166, 190)),
        ('mvThemeCol_TitleBgActive', (22, 163, 74, 255)), ('mvThemeCol_Text', (235, 241, 255, 255)),
    ]

    def __init__(self) -> None:
        self.service = RelayService()
        self._dpg = None

    @property
    def dpg(self) -> Any:
        if self._dpg is None:
            try:
                import dearpygui.dearpygui as dpg

                self._dpg = dpg
            except ModuleNotFoundError as exc:
                raise ImportError('DearPyGui is required to run the GUI. Install dearpygui.') from exc
        return self._dpg

    def _set_status(self, text: str, color=(200, 220, 255, 255)) -> None:
        self.dpg.set_value('status_text', text)
        self.dpg.configure_item('status_text', color=color)

    def _selected_relay_id(self) -> str | None:
        selected = self.dpg.get_value('device_combo')
        return None if selected == 'Default' else selected

    def _scan_devices(self) -> None:
        try:
            devices = self.service.get_devices()
            ids = ['Default'] + [d['device_id'] for d in devices if d.get('device_id')]
            self.dpg.configure_item('device_combo', items=ids)
            self.dpg.set_value('device_combo', ids[0])
            self.dpg.delete_item('device_table', children_only=True, slot=1)
            for dev in devices:
                with self.dpg.table_row(parent='device_table'):
                    self.dpg.add_text(dev.get('device_id', 'Unknown'))
                    self.dpg.add_text('  '.join(f'{k}={v}' for k, v in dev.items() if k.startswith('R')))
            self._set_status(f'Discovered {len(devices)} devices', (120, 255, 170, 255))
        except Exception as exc:
            self._set_status(f'Scan failed: {exc}', (255, 120, 120, 255))

    def _control(self, state: str) -> None:
        relay_number = self.dpg.get_value('relay_input').strip().lower()
        try:
            result = self.service.set_and_get_relay_state(self._selected_relay_id(), relay_number, state)
            self._set_status(f'{self._selected_relay_id() or "Default"} relay {relay_number} => {state.upper()}', (120, 255, 170, 255))
            self.dpg.set_value('output_text', str(result.relay_state))
        except RelayError as exc:
            self._set_status(str(exc), (255, 120, 120, 255))

    def _create_theme(self) -> int:
        with self.dpg.theme() as theme:
            with self.dpg.theme_component(self.dpg.mvAll):
                for item in self.THEME_STYLES:
                    self.dpg.add_theme_style(getattr(self.dpg, item[0]), *item[1:])
                for color, value in self.THEME_COLORS:
                    self.dpg.add_theme_color(getattr(self.dpg, color), value)
        return theme

    def run(self) -> None:
        dpg = self.dpg
        dpg.create_context()
        dpg.bind_theme(self._create_theme())
        with dpg.window(label='HID USB Relay - Control Center', width=410, height=385):
            dpg.add_text('Control Relays Here', color=(0, 230, 200, 255))
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_text('Device')
                dpg.add_combo(['Default'], default_value='Default', width=120, tag='device_combo')
                dpg.add_button(label='Scan Devices', callback=lambda: self._scan_devices())
            with dpg.group(horizontal=True):
                dpg.add_text('Relay')
                dpg.add_input_text(default_value='all', width=90, tag='relay_input')
                dpg.add_button(label='TURN ON', callback=lambda: self._control('on'))
                dpg.add_button(label='TURN OFF', callback=lambda: self._control('off'))
            dpg.add_spacer(height=8)
            dpg.add_text('status', tag='status_text', color=(180, 200, 255, 255))
            dpg.add_input_text(tag='output_text', multiline=True, readonly=True, width=-1, height=60)
            dpg.add_spacer(height=8)
            dpg.add_text('Discovered Devices', color=(255, 215, 120, 255))
            with dpg.table(header_row=True, resizable=True, borders_innerH=True, borders_outerH=True, borders_innerV=True, borders_outerV=True, row_background=True, tag='device_table'):
                dpg.add_table_column(label='Device ID', width_stretch=True)
                dpg.add_table_column(label='Relay States', width_stretch=True)
        dpg.create_viewport(title='HID USB Relay', width=430, height=430)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        self._scan_devices()
        dpg.start_dearpygui()
        dpg.destroy_context()


def run_gui() -> None:
    """Run the desktop GUI application."""

    HIDUSBRelayGUI().run()
