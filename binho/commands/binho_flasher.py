#!/usr/bin/env python3

from __future__ import print_function

import errno
import sys
import logging
from pyocd.core.helpers import ConnectHelper
from pyocd.flash.file_programmer import FileProgrammer
from pyocd.flash.eraser import FlashEraser

from binho.utils import log_silent, log_verbose
from binho.errors import DeviceNotFoundError
from binho.utils import binhoArgumentParser


def main():

    # Set up a simple argument parser.
    parser = binhoArgumentParser(
        description="utility for using supported Binho host adapters in DAPLink mode to flash code to MCUs"
    )

    parser.add_argument("-t", "--target", default=None, help="Manufacturer part number of target device")

    parser.add_argument("-f", "--file", default=None, help="Path to binary file to program")

    parser.add_argument(
        "-e", "--erase", action="store_true", help="Perform chip-erase before programming",
    )

    parser.add_argument(
        "-r", "--reset", action="store_true", help="Reset the device after programming completes",
    )

    args = parser.parse_args()

    log_function = log_verbose if args.verbose else log_silent

    log_function("Checking for pyOCD...")

    try:
        import pyocd  # pylint: disable=import-outside-toplevel

    except ModuleNotFoundError:

        print("PyOCD must be installed for this to work. Use 'pip install pyocd' to install the module.")
        sys.exit(1)

    log_function("pyOCD installation confirmed!")

    try:

        log_function("Trying to find a Binho host adapter...")
        device = parser.find_specified_device()

        if device.inDAPLinkMode:
            log_function(
                "{} found on {} in DAPLink mode (Device ID: {})".format(
                    device.productName, device.commPort, device.deviceID
                )
            )

        else:
            log_function("{} found on {}. (Device ID: {})".format(device.productName, device.commPort, device.deviceID))

            print("The {} is not in DAPLink mode. Please use the 'binho daplink' command ")
            sys.exit(errno.ENODEV)

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

        if not args.file and not (args.erase or args.reset):
            print("No binary file to program was supplied.")
            sys.exit(1)

        erase_setting = "auto"
        target_override = "cortex_m"

        if args.erase:
            erase_setting = "chip"

        if args.target:
            target_override = args.target

        if args.verbose:
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(level=logging.WARNING)

        with ConnectHelper.session_with_chosen_probe(
            target_override=target_override, chip_erase=erase_setting, smart_flash="false",
        ) as session:

            board = session.board
            target = board.target

            print("Vendor: {}\tPart Number: {}".format(target.vendor, target.part_number))

            if args.erase:
                eraser = FlashEraser(session, FlashEraser.Mode.CHIP)
                eraser.erase()
                print("{} erased".format(target.part_number))

            if args.file:
                FileProgrammer(session).program(args.file)
                log_function("Target {} programmed with {}".format(target.part_number, args.file))

            if args.reset:
                target.reset()
                print("Target {} reset".format(target.part_number))

    except pyocd.core.exceptions.TransferError:

        print(
            "Problem communicating with the target MCU. Please make sure SWDIO, SWCLK, and GND are properly "
            " connected and the MCU is powered up."
        )

    finally:

        # close the connection to the host adapter
        device.close()


if __name__ == "__main__":
    main()
