import logging
import asyncio

from bleak import BleakScanner

import python.kraken_uuids as kraken_uuids

async def scan_for_kraken_beacons(scan_duration_seconds=1):
    kraken_list = {}
    
    def detection_callback(device, advertisement_data):
        nonlocal kraken_list
        if kraken_uuids.KRAKEN_SERVICE_UUID in advertisement_data.service_uuids:
            if device.address not in kraken_list.keys():
                logging.info(f"Scanner found new Kraken {device.address}")
                kraken_list[device.address] = {
                    "rssi": advertisement_data.rssi
                }

    scanner = BleakScanner(detection_callback)
    logging.info(f"Performing {scan_duration_seconds} second scan for BLE devices")
    await scanner.start()
    await asyncio.sleep(scan_duration_seconds)
    await scanner.stop()
    logging.info("BLE scan complete")

    await asyncio.sleep(3) # time for BLE stack to recover

    return kraken_list