#!/usr/bin/env python3

from __future__ import print_function

import errno
import sys
import time
import argparse
import statistics
import hid

from binho.utils import log_silent, log_verbose, binho_error_hander, binhoDFUManager
from binho.errors import DeviceNotFoundError


def main():
    from binho.utils import binhoArgumentParser

    # Set up a simple argument parser.
    parser = binhoArgumentParser(
        description="utility for using supported Binho host adapters in DAPLink mode"
    )

    parser.add_argument(
        "-q",
        "--quit",
        action="store_true",
        help="Quit DAPlink mode, return to host adapter mode",
    )

    args = parser.parse_args()

    log_function = log_verbose if args.verbose else log_silent

    try:

        log_function("Trying to find a Binho host adapter...")
        device = parser.find_specified_device()

        if device.inDAPLinkMode:
            print(
                "{} found on {} in DAPLink mode".format(
                    device.productName, device.commPort
                )
            )

        if device.inBootloaderMode:
            print(
                "{} found on {}, but it cannot be used now because it's in DFU mode".format(
                    device.productName, device.commPort
                )
            )
            sys.exit(errno.ENODEV)
        else:
            log_function(
                "{} found on {}. (Device ID: {})".format(
                    device.productName, device.commPort, device.deviceID
                )
            )

    except DeviceNotFoundError:
        if args.serial:
            print(
                "No Binho host adapter found matching Device ID '{}'.".format(
                    args.serial
                ),
                file=sys.stderr,
            )
        else:
            print("No Binho host adapter found!", file=sys.stderr)
        sys.exit(errno.ENODEV)

    # if we fail before here, no connection to the device was opened yet.
    # however, if we fail after this point, we need to make sure we don't
    # leave the serial port open.

    try:

        if args.quit:

            log_function('Returning to host adapter mode... This will cause the device to reset.')

            fwUpdateURL = device.FIRMWARE_UPDATE_URL
            firmwareFileURL = binhoDFUManager.getLatestFirmwareUrl(fwUpdateURL, True)

            binhoDFUManager.downloadFirmwareFile(firmwareFileURL)

            figFileName = binhoDFUManager.getLatestFirmwareFilename(fwUpdateURL)

            binhoDFUManager.takeDrivesSnapshot()

            h = hid.device()
            h.open(0x04D8, 0xED34)  # Binho Nova VendorID/ProductID

            # enable non-blocking mode
            h.set_nonblocking(1)

            # write some data to the device
            # print("Write the data")
            h.write([0x00, 0x80])

            # wait
            time.sleep(5)

            newDrives = binhoDFUManager.getNewDrives()

            binhoDFUManager.loadFirmwareFile(figFileName, newDrives[0])

            log_function('Completed!')

        else:

            log_function('Switching to DAPLink mode... This will cause the device to reset.')

            device.close()

    except Exception:
        # Catch any exception that was raised and display it
        binho_error_hander()

        # close the connection to the host adapter
        device.close()


if __name__ == "__main__":
    main()
