import asyncio
import datetime
import os

from kivy.app import App
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.text import Label as CoreLabel
from kivy.uix.scrollview import ScrollView

# bind bleak's python logger into kivy's logger before importing python module using logging
from kivy.logger import Logger  # isort: skip
import logging  # isort: skip

# import custom_exceptions
# import csv_log

from python.kraken_widget import KrakenWidget
import python.ble_utils as ble_utils
from python import csv_log

# from scan_and_add import ScanAndAddWidget
# from kraken_monitor_subwin import KrakenMonitorSubWindow

# ==============================================================================
# Android Bluetooth set up
# ==============================================================================

if platform == 'android':
    from android.permissions import request_permissions, Permission

    request_permissions([Permission.BLUETOOTH,
        Permission.BLUETOOTH_SCAN,
        Permission.BLUETOOTH_CONNECT,
        Permission.BLUETOOTH_ADMIN,
        Permission.ACCESS_FINE_LOCATION,
        Permission.ACCESS_COARSE_LOCATION,
        Permission.ACCESS_BACKGROUND_LOCATION])

# ==============================================================================
# Set up log and data dir
# ==============================================================================

logging.Logger.manager.root = Logger

if platform == 'android':
    from plyer import storagepath
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

    out_dir = storagepath.get_documents_dir()
    out_dir = os.path.join(out_dir, 'KrakenData')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
else:
    out_dir = os.path.expanduser('Data') # Simply put data in a dir alongside the scripts
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

# ==============================================================================
# Main code
# ==============================================================================

class AppRoot(App):
    def __init__(self):
        super().__init__()
        self.label = None
        self.running = True
        self.sub_windows = []
        self.sub_window_to_close = None
        self.max_tab_width = dp(120)  # start reasonable
        self.font_name = None         # set to your bundled TTF for consistent metrics (see note below)
        self.font_size_sp = 16

        self.kraken_widgets = {}

        self.csv_ble_info_logger = csv_log.CSVLogger(["address", "name", "kraken_rssi", "kraken_power", "kraken_phy", "connection_count", "central_rssi", "central_phy", "channel_map", "available_channels", "current_channel", "connection_interval_ms", "supervision_timeout_ms"], os.path.join(out_dir, f"KrakenBleConnectionData_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"))
        self.csv_event_logger = csv_log.CSVLogger(["source", "event", "notes"], os.path.join(out_dir, f"KrakenEventLog_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"))
        # NOTE: Modify this if you change the format of the data being logged
        self.csv_event_logger.write(['APP', "LOG_VERSION", '1'])


    def build(self):
        self.layout = TabbedPanel(do_default_tab=False)

        self.dashboard_scroll = ScrollView(size_hint=(1, 1))
        # Inner content that actually stacks widgets
        self.dashboard_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(6),
            padding=(dp(10), dp(10))
        )
        # Critical: content height expands to fit children
        self.dashboard_layout.bind(minimum_height=self.dashboard_layout.setter("height"))

        self.dashboard_scroll.add_widget(self.dashboard_layout)
        
        dashboard = TabbedPanelHeader(text="Dashboard")
        dashboard.content = self.dashboard_scroll
        self.layout.add_widget(dashboard)

        return self.layout


    def on_start(self):
        asyncio.create_task(self.run())


    def _measure_text_w(self, text: str) -> float:
        """Measure text width using CoreLabel; add dp padding."""
        kwargs = {
            'text': text,
            'font_size': sp(self.font_size_sp)
        }
        # Only include font_name if you have one
        if self.font_name:
            kwargs['font_name'] = self.font_name

        lbl = CoreLabel(**kwargs)
        lbl.refresh()  # build the texture so texture.size is available
        w, _ = lbl.texture.size
        return w + dp(40)  # padding on both sides


    def add_new_tab(self, address):
        if address in self.kraken_widgets.keys():
            return # Already have a tab, so ignore the request

        def adjust_width(tab, *args):
            tab.width = tab.texture_size[0] + dp(40)

        logging.info(f"Adding new tab for address {address}")
        self.kraken_widgets[address] = KrakenWidget(address, self.csv_ble_info_logger, self.csv_event_logger)
        new_panel = TabbedPanelHeader(text=str(address))
        new_panel.content = self.kraken_widgets[address].build()
        self.layout.add_widget(new_panel)
        tab_width = self._measure_text_w(address) #new_panel.texture_size[0] + dp(40)
        logging.warning(f"Required width = {tab_width}")
        if self.max_tab_width < tab_width:
            logging.warning(f"Adjusting tab size -> {tab_width}")
            self.max_tab_width = tab_width
            self.layout.tab_width = tab_width

        self.dashboard_layout.add_widget(self.kraken_widgets[address].get_dashboard_widget())


    def on_stop(self):
        self.running = False

    # def on_close_sub_window(self, instance):
    #     # NOTE: Iterate over a copy of the list, to allow safe removal
    #     for sw in self.sub_windows[:]:
    #         if sw['close_button'] == instance:
    #             self.sub_window_to_close = sw
    #             return
            
    #     raise Exception("Failed to find instance of sub window to remove!")


    async def run(self):
        while self.running:
            await asyncio.sleep(1)
            krakens_in_range = await ble_utils.scan_for_kraken_beacons()
            for address, data in krakens_in_range.items():
                if address not in self.kraken_widgets.keys():
                    # self.add_new_tab(address)
                    Clock.schedule_once(lambda dt: self.add_new_tab(address))

                if address in self.kraken_widgets.keys():
                    self.kraken_widgets[address].process_beacon_data(data)

            # Execute all runners for subwindows
            # NOTE: Work on a copy since the dictionary size can change while iterating
            opened_widgets = list(self.kraken_widgets.values())
            for k in opened_widgets:
                await k.run()

            # TODO: Would be good to "blink" and LED to indicate things are running ok
        #     new_kraken_address = await self.scan_and_add_widget.run()
        #     if new_kraken_address is not None:
        #         Logger.info("Adding new Kraken")

        #         try:
        #             address = new_kraken_address
        #             Logger.info(f"Got this address from scan and select! {address}")

        #             kraken_monitor_ui = BoxLayout(orientation='horizontal')

        #             kraken_subwindow = KrakenMonitorSubWindow(address, self.csv_logger)
        #             kraken_monitor_ui.add_widget(kraken_subwindow.get_widget())
        #             close_button = Button(text="close", size_hint=(0.05, 1))
        #             kraken_monitor_ui.add_widget(close_button)

        #             close_button.bind(on_press=self.on_close_sub_window)

        #             # TODO: Need to check if we already have a subwindow open!
        #             self.sub_windows.append({
        #                 'address': address,
        #                 'close_button': close_button,
        #                 'widget': kraken_monitor_ui,
        #                 'obj': kraken_subwindow
        #             })

        #             self.layout.add_widget(kraken_monitor_ui)

        #         except custom_exceptions.UserCancelledAction:
        #             pass # no action required
        #         except custom_exceptions.InvalidUserInput:
        #             pass # TODO: toast notification?

        #     if self.sub_window_to_close is not None:
        #         Logger.info("Closing subwindow")
        #         self.layout.remove_widget(self.sub_window_to_close['widget'])
        #         await self.sub_window_to_close['obj'].on_close()
        #         self.sub_windows.remove(self.sub_window_to_close)
        #         self.sub_window_to_close = None

        #     # runners for subwindows
        #     for sw in self.sub_windows:
        #         await sw['obj'].run()

        #     await asyncio.sleep(0.1) # Need to allow time for other processing to take place

        # Logger.error("Performing tidy")
        # for sw in self.sub_windows:
        #     await sw['obj'].on_close()


if __name__ == "__main__":
    Logger.setLevel(logging.DEBUG)

    # app running on one thread with two async coroutines
    app = AppRoot()
    asyncio.run(app.async_run(async_lib="asyncio"))
