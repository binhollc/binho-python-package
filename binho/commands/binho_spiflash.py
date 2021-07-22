#!/usr/bin/env python3

from __future__ import print_function

import errno
import sys

import binho  # pylint: disable=unused-import
from binho import binhoHostAdapter  # pylint: disable=unused-import
from binho.utils import log_silent, log_verbose, binhoArgumentParser
from binho.errors import DeviceNotFoundError


def main():  # pylint: disable=too-many-locals

    # Set up a simple argument parser.
    parser = binhoArgumentParser(description="Utility for working with SPI FLASH memory devices")

    parser.add_argument("-c", "--chipselect", default=0, help="Set CS signal IO pin")

    parser.add_argument(
        "-n", "--invertCS", action="store_true", help="Set CS signal as inverted (Active High)",
    )
    parser.add_argument("-m", "--mode", default=0, help="Set SPI mode")

    parser.add_argument(
        "-f", "--frequency", default=12000000, help="Specifies the frequency for the SPI Clock",
    )

    args = parser.parse_args()

    log_function = log_verbose if args.verbose else log_silent

    try:
        log_function("Trying to find a Binho host adapter...")
        device = parser.find_specified_device()

        if device.inBootloaderMode:
            print(
                "{} found on {}, but it cannot be used now because it's in DFU mode".format(
                    device.productName, device.commPort
                )
            )
            sys.exit(errno.ENODEV)

        elif device.inDAPLinkMode:
            print(
                "{} found on {}, but it cannot be used now because it's in DAPlink mode".format(
                    device.productName, device.commPort
                )
            )
            print("Tip: Exit DAPLink mode using 'binho daplink -q' command")
            sys.exit(errno.ENODEV)

        else:
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

        # set the host adapter operationMode to 'SPI'
        device.operationMode = "SPI"

        if args.frequency:
            log_function("SPI clock set to {}Hz".format(args.frequency))

        if args.mode:

            if int(args.mode) < 0 or int(args.mode) > 3:
                print("SPI mode must be 0, 1, 2, or 3. mode = {} is not a valid setting.".format(args.mode))
                device.close()
                sys.exit(errno.EINVAL)
            else:
                log_function("SPI mode set to mode {}".format(args.mode))

        csPin = {}

        if args.chipselect:
            if args.chipselect.isnumeric():
                chipSelectStr = "IO" + str(args.chipselect)
            else:
                chipSelectStr = args.chipselect

            csPin = device.gpio_pins[chipSelectStr]
        else:
            csPin = None

        if csPin:
            if args.invertCS:
                log_function("Using IO{} as an Active-High (inverted) ChipSelect signal".format(csPin.pin_number))
            else:
                log_function("Using IO{} as an Active-Low (standard) ChipSelect signal".format(csPin.pin_number))
        else:
            log_function(
                "No ChipSelect signal specified, will not be used for this transaction. Use -c to specify IO pin to\
                 use for ChipSelect if desired."
            )

        # Now that we've got the SPI CS pin configuration, let's go ahead and create the programmer object
        # This function accepts a number of parameters, not all shown or demo'd here
        # spiFlash = device.create_programmer(
        #    "spiFlash", chip_select_pin=csPin, autodetect=True, mode=args.mode,
        #    clocK_frequency=args.frequency
        # )

        print("This command is still under construction. Please come back again later!")
        sys.exit(1)

    finally:

        # close the connection to the host adapter
        device.close()


if __name__ == "__main__":
    main()
