#!/usr/bin/env python3

from __future__ import print_function

import errno
import sys
import ast

import binho  # pylint: disable=unused-import
from binho import binhoHostAdapter  # pylint: disable=unused-import
from binho.utils import log_silent, log_verbose, binhoArgumentParser
from binho.interfaces.spiBus import SPIBus
from binho.errors import DeviceNotFoundError


def main():

    # Set up a simple argument parser.
    parser = binhoArgumentParser(description="Utility for SPI communication via Binho host adapter")
    parser.add_argument(
        "-r", "--read", default=0, help="Number of bytes expecting to receive from the SPI Bus",
    )
    parser.add_argument(
        "-w", "--write", nargs="*", type=ast.literal_eval, default=[], help="Bytes to send over the SPI Bus",
    )
    parser.add_argument("-f", "--frequency", default=None, help="Set clock frequency")
    parser.add_argument("-c", "--chipselect", default=0, help="Set CS signal IO pin")
    parser.add_argument(
        "-n", "--invertCS", action="store_true", help="Set CS signal as inverted (Active High)",
    )
    parser.add_argument("-m", "--mode", default=0, help="Set SPI mode")
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

        if args.write or int(args.read) > 0:

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

            transmit(
                device, args.write, int(args.read), csPin, args.invertCS, args.mode, log_function,
            )

        else:
            log_function(
                "No transaction performed. Please specify data to write with '-w' or a number of bytes to read using \
                 '-r'."
            )
            log_function("You can type 'binho spi --help' for more information.")

            # close the connection to the host adapter
            device.close()

    finally:

        # close the connection to the host adapter
        device.close()


def transmit(device, data, receive_length, csPin, invCS, mode, log_function):  # pylint: disable=too-many-arguments
    spi_bus = SPIBus(device)
    result = spi_bus.transfer(data, receive_length, chip_select=csPin, spi_mode=mode, invert_chip_select=invCS)
    log_function("SPI Transfer Completed:")

    sentBytes = "W"
    for byte in data:
        sentBytes += "\t " + "0x{:02x}".format(byte)
    log_function(sentBytes)

    rcvdBytes = "R"
    for byte in result:
        rcvdBytes += "\t " + "0x{:02x}".format(byte)
    log_function(rcvdBytes)


if __name__ == "__main__":
    main()
