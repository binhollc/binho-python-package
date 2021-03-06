#!/usr/bin/env python3

from __future__ import print_function

import errno
import sys

from binho.utils import (
    log_silent,
    log_verbose,
    binhoDFUManager,
    binhoArgumentParser,
)
from binho.errors import DeviceNotFoundError


def main():

    # Set up a simple argument parser.
    parser = binhoArgumentParser(description="utility for updating firmware on Binho host adapters")

    parser.add_argument(
        "-q", "--quit", action="store_true", help="Exit DFU mode, return to normal operation.",
    )

    parser.add_argument(
        "-b",
        "--btldr",
        action="store_true",
        help="Enter DFU mode. Note that this will be done automatically during firmware upgrade commands.",
    )

    parser.add_argument(
        "-l",
        "--latest",
        action="store_true",
        help="Update the firmware of the target device to the latest release available",
    )

    parser.add_argument(
        "-r", "--release", default=None, help="Update the firmware of the desired device to a specific release version",
    )

    args = parser.parse_args()

    log_function = log_verbose if args.verbose else log_silent

    try:

        log_function("Trying to find a Binho host adapter...")
        device = parser.find_specified_device()

        log_function("{} found on {}. (Device ID: {})".format(device.productName, device.commPort, device.deviceID))

    except DeviceNotFoundError:
        if args.serial:
            print(
                "No Binho host adapter found matching Device ID '{}'.".format(args.serial), file=sys.stderr,
            )
        else:
            print("No Binho host adapter found!", file=sys.stderr)
        sys.exit(errno.ENODEV)

    # if we fail before here, no connection to the device was opened yet.
    # however, if we fail after this point, we need to make sure we don't
    # leave the serial port open.

    try:

        if args.quit:

            if device.inBootloaderMode:

                log_function("Exiting bootloader...")
                device.exit_bootloader()
                log_function("Completed!")

            elif device.inDAPLinkMode:

                log_function("{} is not in bootloader, cannot exit!".format(device.productName))
                log_function("Note: You can exit DAPLink mode using the 'binho daplink -q' command.")

            else:

                log_function("{} is not in bootloader, cannot exit!".format(device.productName))
                log_function("Note: You can enter bootloader mode using the 'binho dfu' command.")

        elif args.btldr:

            if device.inBootloaderMode:

                log_function(
                    "{}:{} on {} is already in it's bootloader".format(
                        device.productName, device.deviceID, device.commPort
                    )
                )

            else:
                log_function("Resetting {} into it's bootloader".format(device.productName))
                binhoDFUManager.switchToBootloader(device)
                log_function("Bootloader Details:")
                log_function("Version: {}".format(binhoDFUManager.bootloaderInfo["version"]))
                log_function("Model: {}".format(binhoDFUManager.bootloaderInfo["model"]))
                log_function("BoardID: {}".format(binhoDFUManager.bootloaderInfo["boardID"]))
                log_function("Completed!")

        else:

            if args.latest and args.release:
                print("Invalid arguments. -l/--latest cannot be used with -r/--release")
                sys.exit(1)

            if args.latest:

                log_function("Getting latest firmware release...")
                latestVersion = binhoDFUManager.getLatestFirmwareVersion(device.FIRMWARE_UPDATE_URL)
                log_function("Latest Version: {}".format(latestVersion))

                if device.firmwareVersion == latestVersion:

                    print("This {} is already running the latest firmware.".format(device.productName))

                else:

                    log_function("Updating device...")
                    binhoDFUManager.switchToNormal(device)
                    log_function("Firmware Update Complete!")

            elif args.release:

                if device.firmwareVersion == args.release:
                    print(
                        "This {} is already running firmware version {}.".format(
                            device.productName, device.firmwareVersion
                        )
                    )

                else:

                    log_function("Looking for {} Release...".format(args.release))
                    is_available = binhoDFUManager.isFirmwareVersionAvailable(device.FIRMWARE_UPDATE_URL, args.release)

                    if not is_available:
                        print("{} is not available.".format(args.release))
                        sys.exit(1)

                    log_function("Found it. Preparing to update device.")

                    binhoDFUManager.switchToNormal(device, args.release)
                    log_function("Firmware Update Complete!")

    finally:
        # close the connection to the host adapter
        device.close()


if __name__ == "__main__":
    main()
