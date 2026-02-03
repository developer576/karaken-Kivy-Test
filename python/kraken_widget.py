import logging

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

import numpy as np
from bleak import BleakClient

import python.kraken_uuids as kraken_uuids
from python.sl_status_code_parser import sl_status_to_string

class KrakenWidget:
    def __init__(self, address, connection_info_csv_logger, csv_event_logger):
        # Outer container can just be the ScrollView
        self.scroll = ScrollView(size_hint=(1, 1))

        # Inner content that actually stacks widgets
        self.layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(6),
            padding=(dp(10), dp(10))
        )
        # Critical: content height expands to fit children
        self.layout.bind(minimum_height=self.layout.setter("height"))

        self.scroll.add_widget(self.layout)

        
        # state
        self.current_mode = "beacon"
        self.name = None
        self.fw_ver = None
        self.address = address
        self.central_rssi = '?'
        self.ble_client = None

        self.connection_info_csv_logger = connection_info_csv_logger
        self.csv_event_logger = csv_event_logger

        # widgets
        # Simple function to create consistent label widgets
        def _create_simple_label_widget(text):
            lbl = Label(text=text, 
                        markup=True, 
                        size_hint=(1, None),
                        text_size=(None, None),
                        halign='left',
                        valign='middle',
                        font_size='18sp')
            
            # Make text wrap to label width and compute height from texture
            lbl.bind(
                width=lambda inst, w: setattr(inst, "text_size", (w, None)),
                texture_size=lambda inst, ts: setattr(inst, "height", max(ts[1], dp(28)))
            )
            # initial text_size
            lbl.text_size = (lbl.width, None)

            return lbl


        self.current_mode_label = _create_simple_label_widget(text="Current Mode: Beacon")
        self.device_name_label = _create_simple_label_widget(text="Device Name: ?")
        self.fw_ver_label = _create_simple_label_widget(text="FW Version: ?")

        self.kraken_rssi_label = _create_simple_label_widget(text="Kraken RSSI: ?")
        self.kraken_current_power_label = _create_simple_label_widget(text="Kraken Current Power: ?")
        self.kraken_max_power_label = _create_simple_label_widget(text="Kraken Max Power: ?")
        self.kraken_phy_label = _create_simple_label_widget(text="Kraken Phy: ?")
        self.kraken_open_connection_count_label = _create_simple_label_widget(text="Open Connections: ?")
        self.kraken_last_disconnect_reason_label = _create_simple_label_widget(text="Last Disconnect reason: ?")

        self.central_rssi_label = _create_simple_label_widget(text="Central RSSI: ?")
        self.central_phy_label = _create_simple_label_widget(text="Central Phy: ?")
        
        self.ble_channel_map_label = _create_simple_label_widget(text="Channel Map: ?")
        self.ble_current_channel_label = _create_simple_label_widget(text="Current Channel: ?")
        self.ble_connection_interval_label = _create_simple_label_widget(text="Connection Interval: ?")
        self.ble_supervision_timeout_label = _create_simple_label_widget(text="Supervision Timeout: ?")

        self.latest_pressure_label = _create_simple_label_widget(text="Latest Pressure: ?")

        self.csv_event_logger.write([self.address, "kraken_widget_created", ""])

        self.dashboard_widget = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(6),
            padding=(dp(10), dp(10))
        )
        self.dashboard_widget.bind(minimum_height=self.dashboard_widget.setter("height"))
        
        self.dashboard_name_label = _create_simple_label_widget("Name: ?")
        self.dashboard_widget.add_widget(self.dashboard_name_label)
        self.dashboard_mode_label = _create_simple_label_widget("Mode: Beacon")
        self.dashboard_widget.add_widget(self.dashboard_mode_label)
        self.dashboard_address_label = _create_simple_label_widget(f"Address: {address}")
        self.dashboard_widget.add_widget(self.dashboard_address_label)
        self.dashboard_kraken_rssi_label = _create_simple_label_widget("Kraken RSSI: ?")
        self.dashboard_widget.add_widget(self.dashboard_kraken_rssi_label)
        self.dashboard_central_rssi_label = _create_simple_label_widget("Central RSSI: ?")
        self.dashboard_widget.add_widget(self.dashboard_central_rssi_label)

    def build(self):
        self.show_ui()

        return self.scroll


    def get_dashboard_widget(self):
        return self.dashboard_widget


    def show_ui(self):
        self.layout.clear_widgets()

        def _create_simple_heading_widget(text):
            lbl = Label(text=f"[b][u]{text}[/u][/b]", 
                        markup=True, 
                        size_hint=(1, None),
                        text_size=(None, None),
                        halign='left',
                        valign='middle',
                        font_size='28sp')
            
            # Make text wrap to label width and compute height from texture
            lbl.bind(
                width=lambda inst, w: setattr(inst, "text_size", (w, None)),
                texture_size=lambda inst, ts: setattr(inst, "height", max(ts[1], dp(28)))
            )
            # initial text_size
            lbl.text_size = (lbl.width, None)

            return lbl
        
        def _create_simple_subheading_widget(text):
            lbl = Label(text=f"[b]{text}[/b]", 
                        markup=True, 
                        size_hint=(1, None),
                        text_size=(None, None),
                        halign='left',
                        valign='middle',
                        font_size='22sp')
            
            # Make text wrap to label width and compute height from texture
            lbl.bind(
                width=lambda inst, w: setattr(inst, "text_size", (w, None)),
                texture_size=lambda inst, ts: setattr(inst, "height", max(ts[1], dp(28)))
            )
            # initial text_size
            lbl.text_size = (lbl.width, None)

            return lbl

        # Define the UI layout
        self.layout.add_widget(self.current_mode_label)
        self.layout.add_widget(self.device_name_label)
        self.layout.add_widget(self.fw_ver_label)

        self.layout.add_widget(_create_simple_heading_widget("BLE Connection Info"))
        self.layout.add_widget(_create_simple_subheading_widget("Kraken Side"))
        self.layout.add_widget(self.kraken_rssi_label)
        self.layout.add_widget(self.kraken_open_connection_count_label)
        self.layout.add_widget(self.kraken_phy_label)
        self.layout.add_widget(self.kraken_current_power_label)
        self.layout.add_widget(self.kraken_max_power_label)
        self.layout.add_widget(self.kraken_last_disconnect_reason_label)

        self.layout.add_widget(_create_simple_subheading_widget("Central Side"))
        self.layout.add_widget(self.central_rssi_label)
        self.layout.add_widget(self.central_phy_label)

        self.layout.add_widget(_create_simple_subheading_widget("Environment"))
        self.layout.add_widget(self.ble_channel_map_label)
        self.layout.add_widget(self.ble_current_channel_label)
        self.layout.add_widget(self.ble_connection_interval_label)
        self.layout.add_widget(self.ble_supervision_timeout_label)

        self.layout.add_widget(_create_simple_heading_widget("Standard Data Stream"))
        self.layout.add_widget(self.latest_pressure_label)

    # ==========================================================================
    # Callbacks
    # ==========================================================================

    def process_beacon_data(self, data):
        # TODO: Get the advertised name and populate thiss
        self.central_rssi = data['rssi']
        self.central_rssi_label.text = f"Central RSSI: {self.central_rssi} dBm"
        self.dashboard_central_rssi_label.text = f"Central RSSI: {self.central_rssi} dBm"


    def _process_pressure_data_notification(self, sender, data):
        interpreted_data = PressureData(data)
        logging.debug(interpreted_data)
        self.latest_pressure_label.text = f"Latest Pressure: {interpreted_data.pressure} PSI"


    def _process_ble_connection_info_notification(self, sender, data):
        def phy_id_to_desc(id):
            lookup = {
                1: "1M",
                2: "2M",
                4: "Coded PHY - 125k (S=8) or 500k (S=2)"
            }
            if id in lookup.keys():
                return lookup[id]
            else:
                return id
            
        # TODO: Check the len matches expectations
        interpreted_data = {
            "kraken_rssi": np.frombuffer(data, dtype=np.int8, count=1)[0],
            "kraken_current_power": np.frombuffer(data, dtype=np.int8, count=2)[1],
            "kraken_max_power": data[2],
            "channel_map": (data[3] << (4*8)) | (data[4] << (3*8)) | (data[5] << (2*8)) | (data[6] << (1*8)) | (data[7]),
            "current_channel": data[8],
            "connection_interval_ms": ((data [9] << 8) | data[10]) * 1.25,
            "supervision_timeout_ms": ((data[11] << 8) | data[12]) * 10,
            "central_phy": phy_id_to_desc(data[13]),
            "kraken_phy": phy_id_to_desc(data[14]),
            "last_disconnect_reason": sl_status_to_string((data[15] << 8) | data[16]),
            "open_connections": data[17]
        }
        logging.debug(f"{self.address} BLE connection info -> {interpreted_data}")

        # Do some extra processing to improve UI
        channel_count = 0
        working_channel_map = interpreted_data["channel_map"]
        for i in range(8*5):
            if working_channel_map & 0x01:
                channel_count += 1
            working_channel_map >>= 1

        self.connection_info_csv_logger.write([self.address, 
                                              self.name,
                                              interpreted_data['kraken_rssi'],
                                              interpreted_data['kraken_current_power'],
                                              interpreted_data['kraken_phy'],
                                              interpreted_data['open_connections'],
                                              self.central_rssi, # gathered from beacon data
                                              interpreted_data['central_phy'],
                                              f"0x{interpreted_data['channel_map']:X}",
                                              channel_count,
                                              interpreted_data['current_channel'],
                                              interpreted_data['connection_interval_ms'],
                                              interpreted_data['supervision_timeout_ms']])
        

        # Update UI
        self.kraken_rssi_label.text = f"Kraken RSSI: {interpreted_data['kraken_rssi']} dBm"
        self.kraken_current_power_label.text = f"Kraken Current Power: {interpreted_data['kraken_current_power']} dB"
        self.kraken_max_power_label.text = f"Kraken Max Power: {interpreted_data['kraken_max_power']} dB"
        self.ble_channel_map_label.text = f"Channel Map: 0x{interpreted_data['channel_map']:X} ({channel_count} channels available)"
        self.ble_current_channel_label.text = f"Current Channel: {interpreted_data['current_channel']}"
        self.ble_connection_interval_label.text = f"Connection Interval: {interpreted_data['connection_interval_ms']} ms"
        self.ble_supervision_timeout_label.text = f"Supervision Timeout: {interpreted_data['supervision_timeout_ms']} ms"
        self.central_phy_label.text = f"Central Phy: {interpreted_data['central_phy']}"
        self.kraken_phy_label.text = f"Kraken Phy: {interpreted_data['kraken_phy']}"
        self.kraken_last_disconnect_reason_label.text = f"Last Disconnect Reason: {interpreted_data['last_disconnect_reason']}"
        self.kraken_open_connection_count_label.text = f"Open Connections: {interpreted_data['open_connections']}"

        self.dashboard_kraken_rssi_label.text = f"Kraken RSSI: {interpreted_data['kraken_rssi']} dBm"


    def _disconnect_callback(self, client):
        self.current_mode = "Beacon"
        self.current_mode_label.text = f"Current Mode: Beacon"
        self.dashboard_mode_label.text = f"Current Mode: Beacon"
        self.csv_event_logger.write([self.address, "kraken_disconnected", ""])


    # ==========================================================================
    # GATT Helpers
    # ==========================================================================
    async def _get_kraken_display_name(self):
        legacy_kraken_service = self.ble_client.services.get_service(kraken_uuids.KRAKEN_SERVICE_UUID)
        display_name_char = legacy_kraken_service.get_characteristic(kraken_uuids.KRAKEN_DISPLAY_NAME_CHAR_UUID)
        return (await self.ble_client.read_gatt_char(display_name_char)).decode('ascii')
    
    async def _get_fw_version_number(self):
        device_info_service = self.ble_client.services.get_service(kraken_uuids.DEVICE_INFO_SERVICE_UUID)
        fw_ver_char = device_info_service.get_characteristic(kraken_uuids.UUID_FW_REV_CHAR)
        return (await self.ble_client.read_gatt_char(fw_ver_char)).decode('utf-8').rstrip('\x00')

    # ==========================================================================
    # Run
    # ==========================================================================

    async def run(self):
        if not self.ble_client:
            logging.info(f"Attempting to connect to Kraken {self.address}")
            try:
                self.ble_client = BleakClient(self.address, disconnect_callback=self._disconnect_callback)
                await self.ble_client.connect()
                logging.info(f"Connected to Kraken {self.address}, enabling notifications")
                self.csv_event_logger.write([self.address, "kraken_connected", ""])
                self.current_mode = "Connected"
                self.current_mode_label.text = f"Current Mode: Connected"
                self.dashboard_mode_label.text = f"Current Mode: Connected"

                self.name = await self._get_kraken_display_name()
                self.fw_ver = await self._get_fw_version_number()
                self.device_name_label.text = f"Device Name: {self.name}"
                self.dashboard_name_label.text = f"Device Name: {self.name}"
                self.fw_ver_label.text = f"FW Version: {self.fw_ver}"

                if self.ble_client.services.get_characteristic(kraken_uuids.BLE_CONNECTION_INFO_CHAR_UUID):
                    logging.info(f"Subscribing to BLE connection info notifications for Kraken {self.address}")
                    await self.ble_client.start_notify(kraken_uuids.BLE_CONNECTION_INFO_CHAR_UUID, self._process_ble_connection_info_notification)
                else:
                    logging.warning(f"Kraken {self.address} does not support BLE connection info notifications")
                
                logging.info(f"Enable standard pressure notifications for Kraken {self.address}")
                await self.ble_client.start_notify(kraken_uuids.PRESSURE_SUBSCRIPTION_CHAR_UUID, self._process_pressure_data_notification)
            except Exception as e:
                logging.warning(f"Failed to connect to Kraken {self.address} ({e})")


# ==============================================================================
# Other Helpers
# ==============================================================================

class PressureData:
    def __init__(self, notification_data):
        self._notification_data = notification_data

        kraken_index = 0
        self.name = self.bin2string(notification_data[kraken_index:kraken_index + 16], 16)
        self.pressure = self.reading_to_psi(notification_data[kraken_index + 16:kraken_index + 21])
        self.address = ':'.join(hex(ord(chr(b)))[2:].upper() for b in notification_data[kraken_index + 21:kraken_index + 27])
        self.battery = self.get_battery_reading(notification_data[kraken_index + 27])
        self.scanner_tick = notification_data[kraken_index + 28]
        if len(notification_data) > 29:
            self.charging_state = notification_data[kraken_index + 29]
        else:
            self.charging_state = None

    def bin2string(self, byte_array, length):
        result = ''
        for i in range(length):
            if byte_array[i] == 0:
                break
            result += chr(byte_array[i])
        return result

    def bytes_to_string(self, byte_array):
        return ''.join(chr(b) for b in byte_array)

    def reading_to_psi(self, byte_array):
        try:
            return int(byte_array.decode('utf-8').rstrip('\x00'))/10
        except:
            # simply return the string as a backup (could indicate error state)
            return byte_array.decode('utf-8')

    def get_battery_reading(self, value):
        if value == 255:
            return "Charging.."
        else:
            return f"{value}%"