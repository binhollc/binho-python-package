#!/usr/bin/env python

from __future__ import print_function

import textwrap
import argparse
import errno
import sys

from binho import binhoHostAdapter
from ..utils import binhoDFUManager


def print_core_info(device):
    """ Prints the core information for a device. """

    if device.inBootloaderMode:
        print("Found a {}".format(device.productName) + " [in DFU Mode]")
        print("  Port: {}".format(device.commPort))
        print("  Device ID: {}".format(device.deviceID))
        print(
            "  Note: This device is in DFU Mode! It will not respond to USB commands until a firmware update\n\r"
            "        is completed or it is power cycled."
        )

    elif device.inDAPLinkMode:
        print("Found a {}".format(device.productName) + " [in DAPLink Mode]")
        print("  Port: {}".format(device.commPort))
        print("  Device ID: {}".format(device.deviceID))
        print(
            "  Note: This device is in DAPlink Mode! It can be returned to host adapter (normal) mode\n\r"
            "        by issuing 'binho daplink -q' command."
        )

    else:
        fwVersion = device.firmwareVersion
        print("Found a {}".format(device.productName))
        print("  Port: {}".format(device.commPort))
        print("  Device ID: {}".format(device.deviceID))
        print("  CMD Version: {}".format(device.commandVersion))

        if device.FIRMWARE_UPDATE_URL:
            latestVersion = binhoDFUManager.getLatestFirmwareVersion(device.FIRMWARE_UPDATE_URL, True)

            if latestVersion:
                (latestVerMajor, latestVerMinor, latestVerRev,) = binhoDFUManager.parseVersionString(latestVersion)
                (currVerMajor, currVerMinor, currVerRev,) = binhoDFUManager.parseVersionString(fwVersion)

                newFwVerAvail = False
                if currVerMajor < latestVerMajor:
                    newFwVerAvail = True
                elif currVerMinor < latestVerMinor:
                    newFwVerAvail = True
                elif currVerRev < latestVerRev:
                    newFwVerAvail = True

                if newFwVerAvail:
                    print(
                        "  Firmware Version: {} [A newer version is available! Use 'binho dfu' shell command to "
                        "update.]".format(fwVersion)
                    )
                else:
                    print("  Firmware Version: {} [Up To Date]".format(fwVersion))
            else:
                print("  Firmware Version: {}".format(fwVersion))
        else:
            print("  Firmware Version: {}".format(fwVersion))

    # If this board has any version warnings to display, dipslay them.
    warnings = device.version_warnings()
    if warnings:
        wrapped_warnings = textwrap.wrap(warnings)
        wrapped_warnings = "\n".join(["    {}".format(line) for line in wrapped_warnings])
        print("\n  !!! WARNING !!!\n{}\n".format(wrapped_warnings))


def main():

    # Set up a simple argument parser.
    parser = argparse.ArgumentParser(
        description="Utility for gathering information about connected Binho host Adapters"
    )

    parser.add_argument(
        "-q",
        "--quiet",
        dest="quiet",
        action="store_true",
        help="Prints only the device name and port of detected Binho host adapters",
    )
    args = parser.parse_args()

    # Try to find all existing devices
    devices = binhoHostAdapter(find_all=True)

    if not devices:
        print("No Binho host adapters found!", file=sys.stderr)
        sys.exit(errno.ENODEV)

    # Print the board's information...
    for device in devices:

        if device.inBootloaderMode:
            if args.quiet:
                print(device.productName + " [DFU] (" + device.commPort + ")")
                device.close()
                continue

            # Otherwise, print the core information.
            print_core_info(device)

        elif device.inDAPLinkMode:
            if args.quiet:
                print(device.productName + " [DAPLink] (" + device.commPort + ")")
                device.close()
                continue

            print_core_info(device)

        else:
            # If we're in quiet mode, print only the serial number and abort.
            if args.quiet:
                print(device.productName + " (" + device.commPort + ")")
                device.close()
                continue

            # Otherwise, print the core information.
            print_core_info(device)

        print(" ")

        device.close()


if __name__ == "__main__":
    main()
