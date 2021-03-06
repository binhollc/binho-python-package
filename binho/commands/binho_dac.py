#!/usr/bin/env python3
from __future__ import print_function

import errno
import sys

import binho  # pylint: disable=unused-import
from binho import binhoHostAdapter  # pylint: disable=unused-import
from binho.utils import log_silent, log_verbose, binhoArgumentParser
from binho.errors import DeviceNotFoundError


def main():

    # Set up a simple argument parser.
    parser = binhoArgumentParser(description="Utility for experimenting with Binho host adapters on-board DAC")
    parser.add_argument(
        "-f",
        "--format",
        dest="format",
        type=str,
        default="voltage",
        choices=["voltage", "raw"],
        help="Format for the input.\nVoltage string, or binary value to be loaded into the DAC.",
    )
    parser.add_argument(
        "value",
        metavar="[value]",
        type=float,
        help="The desired voltage (default) or raw value to load into DAC (with -f raw).",
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

        pinNumber = device.dac.getDefaultDACPin()

        if args.format == "voltage":

            device.dac.setOutputVoltage(args.value)
            log_function("DAC channel {} set to {} Volts".format(pinNumber, args.value))

        else:
            device.dac.setOutputRaw(int(args.value))
            log_function("DAC channel {} set to {}".format(pinNumber, int(args.value)))

    finally:
        # close the connection to the host adapter
        device.close()


if __name__ == "__main__":
    main()
