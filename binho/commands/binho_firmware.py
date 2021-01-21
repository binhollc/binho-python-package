#!/usr/bin/env python3

from __future__ import print_function

import errno
import sys
import time
import argparse
import statistics
from binho.utils import log_silent, log_verbose, binho_error_hander, binhoDFUManager
from binho.errors import DeviceNotFoundError


def main():
    from binho.utils import binhoArgumentParser

    # Set up a simple argument parser.
    parser = binhoArgumentParser(
        description="utility for updating firmware on Binho host adapters"
    )
    parser.add_argument(
        "-r",
        "--release",
        default=None,
        help="Provide the desired firmware release version",
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Update the firmware of the target device",
    )
    parser.add_argument(
        "-m",
        "--mode",
        default="app",
        help="Select the mode to update: 'app' for normal host adapter operation or 'dap' for DAPLink operation",
    )

    args = parser.parse_args()

    log_function = log_verbose if args.verbose else log_silent

    try:
        if not(args.mode == 'app' or args.mode == 'dap'):
            print("Invalid 'mode' parameter. Only 'app' and 'dap' are supported!")
            sys.exit(1)

        log_function("Trying to find a Binho host adapter...")
        device = parser.find_specified_device()

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

        if args.mode == 'dap':

            log_function('Downloading DAPLink Firmware...')
            binhoDFUManager.switchToDAPLink(device)
            log_function('Completed!')

        else:

            # Get the version of firmware on the target device
            fwVersion = device.firmwareVersion
            fwUpdateURL = device.FIRMWARE_UPDATE_URL

            print(args.mode)

            # Now check the latest version
            latestVersion = binhoDFUManager.getLatestFirmwareVersion(fwUpdateURL, True)
            firmwareFileURL = binhoDFUManager.getLatestFirmwareUrl(fwUpdateURL, True)

            if latestVersion:
                (
                    latestVerMajor,
                    latestVerMinor,
                    latestVerRev,
                ) = binhoDFUManager.parseVersionString(latestVersion)
                currVerMajor, currVerMinor, currVerRev = binhoDFUManager.parseVersionString(
                    fwVersion
                )

                newFwVerAvail = False
                if currVerMajor < latestVerMajor:
                    newFwVerAvail = True
                elif currVerMinor < latestVerMinor:
                    newFwVerAvail = True
                elif currVerRev < latestVerRev:
                    newFwVerAvail = True

                if newFwVerAvail:

                    if args.update:

                        binhoDFUManager.downloadFirmwareFile(firmwareFileURL)

                        figFileName = binhoDFUManager.getLatestFirmwareFilename(fwUpdateURL)

                        binhoDFUManager.takeDrivesSnapshot()

                        device.reset_to_bootloader()
                        time.sleep(5)

                        newDrives = binhoDFUManager.getNewDrives()

                        binhoDFUManager.loadFirmwareFile(figFileName, newDrives[0])

                    else:

                        log_function(
                            "Firmware Version: {} [A newer version is available! Use 'binho firmware' shell command to " \
                             "update]".format(
                                fwVersion
                            )
                        )
                else:
                    log_function("Firmware Version: {} [Up To Date]".format(fwVersion))
            else:
                log_function("Firmware Version: {}".format(fwVersion))

            daplinkUpdateURL = device.DAPLINK_UPDATE_URL

            version = binhoDFUManager.getLatestFirmwareVersion(daplinkUpdateURL)
            url = binhoDFUManager.getLatestFirmwareUrl(daplinkUpdateURL)
            name = binhoDFUManager.getLatestFirmwareFilename(daplinkUpdateURL)
            binhoDFUManager.downloadFirmwareFile(url)

            print(version)
            print(url)
            print(name)

            device.close()

    except Exception:
        # Catch any exception that was raised and display it
        binho_error_hander()

        # close the connection to the host adapter
        device.close()


if __name__ == "__main__":
    main()
