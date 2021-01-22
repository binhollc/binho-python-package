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

        elif device.inBootloaderMode:
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

            if device.inDAPLinkMode:

                log_function('Returning to host adapter mode... This will cause the device to reset.')
                binhoDFUManager.switchToNormal(device)
                log_function('Completed!')

            else:

                log_function('{} is not in DAPLink mode.'.format(device.productName))

        else:

            if device.inDAPLinkMode:

                log_function('{} is already in DAPLink mode.'.format(device.productName))

            else:

                log_function('Switching to DAPLink mode... This will cause the device to reset.')
                binhoDFUManager.switchToDAPLink(device)
                log_function('Completed!')

        device.close()

    except Exception:
        # Catch any exception that was raised and display it
        binho_error_hander()

        # close the connection to the host adapter
        device.close()


if __name__ == "__main__":
    main()
