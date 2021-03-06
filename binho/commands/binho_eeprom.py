#!/usr/bin/env python3

from __future__ import print_function

import os
import errno
import sys
import time

from intelhex import IntelHex
import binho  # pylint: disable=unused-import
from binho import binhoHostAdapter  # pylint: disable=unused-import
from binho.utils import log_silent, log_verbose, binhoArgumentParser
from binho.errors import DeviceNotFoundError


def main():  # pylint: disable=too-many-locals

    # Set up a simple argument parser.
    parser = binhoArgumentParser(description="Utility for working with I2C EEPROMs")
    parser.add_argument(
        "-u", "--pullup", action="store_true", help="Enable 2.2k pullup resistors (3.3V)",
    )

    parser.add_argument(
        "-n",
        "--partnumber",
        default=None,
        help="Look up device parameters based on EEPROM manufacturer part number. These parameters can be provided \
              individually.",
    )

    parser.add_argument(
        "-f", "--frequency", default=400000, help="Max supported clock frequency of the EEPROM",
    )
    parser.add_argument(
        "-a",
        "--address",
        default=0,
        help="Offset from base address set on pins A0-A2, if present on package. Defaults to 0b000",
    )
    parser.add_argument("-c", "--capacity", default=None, type=int, help="EEPROM capacity in bytes")
    parser.add_argument("-t", "--writetime", default=0.005, type=float, help="EEPROM write cycle time")
    parser.add_argument(
        "-m",
        "--bitmask",
        default="AAA",
        help="Bitmask to determine how to use lowest three bits of EEPROM I2C Address",
    )
    parser.add_argument("-g", "--pagesize", default=None, type=int, help="EEPROM page size in bytes")

    parser.add_argument(
        "-b",
        "--blank",
        action="store_true",
        help="Check if the EEPROM is blank. No other operation will be performed.",
    )
    parser.add_argument("-e", "--erase", action="store_true", help="Erase the EEPROM before writing")
    parser.add_argument(
        "-y", "--verify", action="store_true", help="Verify the EEPROM contents after writing",
    )

    parser.add_argument(
        "-r", "--read", default=None, type=str, help="Read EEPROM data and save it to the provided file",
    )
    parser.add_argument(
        "-w", "--write", default=None, type=str, help="Write the data from the provided file to the EEPROM",
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

        t0 = time.time()  # pylint: disable=unused-variable

        ih = IntelHex()  # pylint: disable=unused-variable
        programmer = []  # pylint: disable=unused-variable
        device.operationMode = "I2C"

        if args.partnumber:
            # programmer = device.create_programmer('eeprom', device='24FC512')
            log_function("Using predefined parameters for EEPROM part number {}".format(args.partnumber.upper()))
            programmer = device.create_programmer("eeprom", device=args.partnumber.upper())

        elif args.frequency and args.capacity and args.writetime and args.bitmask and args.pagesize:
            log_function("EEPROM manually defined:")
            log_function(
                "Max Clock Frequency: {}, Base Address Offset: {}, Bitmask: {}".format(
                    args.frequency, args.address, args.bitmask
                )
            )
            log_function(
                "Capacity: {} bytes, Page Size: {} bytes, Write Cycle Time: {} s".format(
                    args.capacity, args.pagesize, args.writetime
                )
            )

            programmer = device.create_programmer(
                "eeprom",
                args.capacity,
                args.pagesize,
                bitmask=str(args.bitmask),
                slave_address=args.address,
                write_cycle_length=args.writetime,
            )

        else:
            log_function("EEPROM part number not provided, parameters must be manually supplied.")
            log_function("Flags -f, -a, -c, -t, -m, -g should be used to supply the device parameters")
            log_function("when the device part number cannot be used.")
            device.close()
            sys.exit(1)

        log_function("")

        if args.pullup:
            log_function(
                "Engaging the internal 2.2kOhm PullUp resistors. (Pulled to 3.3V). Remove the '-u' flag to rely on "
                "external resistors."
            )
            device.i2c.useInternalPullUps = True
        else:
            log_function(
                "Internal 2.2kOhm PullUp resistors are disengaged. Add the '-u' flag to engage the internal resistors."
            )
            device.i2c.useInternalPullUps = False

        log_function("")

        if args.read and args.write:
            log_function(
                "Cannot perform read and write in the same operation! Please perform these operations separately"
            )
            device.close()
            sys.exit(1)

        if args.verify and not args.write:
            log_function("Cannot perform verify without writing a file at this time.")
            device.close()
            sys.exit(1)

        if args.blank:
            log_function("Checking if the EEPROM is blank...")
            t_start = time.time()
            isBlank = programmer.blankCheck()
            t_stop = time.time()
            elapsedTime = "%.3f" % (t_stop - t_start)

            if isBlank:
                log_function("EEPROM is blank! Elapsed time: {} seconds".format(elapsedTime))
                device.close()
                sys.exit(0)
            else:
                log_function("EEPROM is NOT blank! Elapsed time: {} seconds".format(elapsedTime))
                device.close()
                sys.exit(1)

        if args.erase:
            log_function("Erasing the EEPROM...")
            te_start = time.time()
            programmer.erase()
            te_stop = time.time()
            elapsedTime = "%.3f" % (te_stop - te_start)
            log_function("EEPROM Erase completed! Elapsed time: {} seconds".format(elapsedTime))

        if args.read:
            filename, file_extension = os.path.splitext(args.read)  # pylint: disable=unused-variable

            fileFormat = "bin"
            if file_extension == ".hex":
                fileFormat = "hex"

            log_function("Reading from the EEPROM...")
            tr_start = time.time()
            programmer.readToFile(args.read, format=fileFormat)
            tr_stop = time.time()
            elapsedTime = "%.3f" % (tr_stop - tr_start)
            log_function("EEPROM Read completed! Elapsed time: {} seconds".format(elapsedTime))
            log_function("EEPROM Data saved as {} file to : {}".format(fileFormat, args.read))

        if args.write:

            filename, file_extension = os.path.splitext(args.write)

            fileFormat = "bin"
            if file_extension == ".hex":
                fileFormat = "hex"

            log_function("Writing Data to EEPROM from {} file: {}".format(fileFormat, args.write))
            tw_start = time.time()
            programmer.writeFromFile(args.write, format=fileFormat)
            tw_stop = time.time()
            elapsedTime = "%.3f" % (tw_stop - tw_start)
            log_function("EEPROM Write completed! Elapsed time: {} seconds".format(elapsedTime))

        if args.verify:

            log_function("Verifying Data written to EEPROM from {} file: {}".format(fileFormat, args.write))
            ty_start = time.time()
            programmer.verifyFile(args.write, format=fileFormat)
            ty_stop = time.time()
            elapsedTime = "%.3f" % (ty_stop - ty_start)
            log_function("EEPROM Verify completed! Elapsed time: {} seconds".format(elapsedTime))

    finally:
        # close the connection to the host adapter
        device.close()


if __name__ == "__main__":
    main()
