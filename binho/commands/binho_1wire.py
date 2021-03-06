#!/usr/bin/env python3

from __future__ import print_function

import errno
import sys
import ast

import binho  # pylint: disable=unused-import
from binho import binhoHostAdapter  # pylint: disable=unused-import
from binho.utils import log_silent, log_verbose, binhoArgumentParser
from binho.interfaces.oneWireDevice import OneWireDevice
from binho.errors import DeviceNotFoundError, BinhoException


def main():

    # Set up a simple argument parser.
    parser = binhoArgumentParser(description="Utility for 1-Wire communication via Binho host adapter")
    parser.add_argument("-n", "--iopin", default=0, help="Use the given IO pin number for the 1Wire bus")
    parser.add_argument("-u", "--pullup", action="store_true", help="Enable 2.2k pullup resistor (3.3V)")
    parser.add_argument(
        "-r", "--read", default=0, help="Number of bytes expecting to receive from the 1Wire Bus",
    )
    parser.add_argument(
        "-w", "--write", nargs="*", type=ast.literal_eval, default=[], help="Bytes to send over the 1Wire Bus",
    )
    parser.add_argument("-k", "--skip", action="store_true", help="SKIP device selection")
    parser.add_argument("-z", "--search", action="store_true", help="Search")
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

        device.oneWire.begin(args.iopin, args.pullup)

        if args.search:
            address = device.oneWire.search()

            full_addr = "0x"
            for byte in address:
                full_addr += "{:02x}".format(byte)

            log_function("Search discovered device with address = {}".format(full_addr))

        if args.write and args.read:
            transfer(device, args.skip, args.write, int(args.read), log_function)
        elif args.write:
            write(device, args.skip, args.write, log_function)
        elif args.read:
            read(device, args.skip, int(args.read), log_function)

    finally:
        # close the connection to the host adapter
        device.close()


def transfer(device, skip, data, receive_length, log_function):
    """
    Write data to connected 1Wire device and then read from it in a single transaction
    """

    onewire_device = OneWireDevice(device.oneWire)

    command = "SELECT"
    if skip:
        command = "SKIP"

    try:
        received_data = onewire_device.transfer(data, receive_length, command)
    except BinhoException:
        log_function("1Wire transfer status: fail")
        return

    log_function("1Wire transfer status: success")
    log_function("")
    log_function("Wrote {} byte(s):".format(len(data)))
    log_function("")
    sentBytes = ""
    for byte in data:
        sentBytes += "\t " + "0x{:02x}".format(byte)
    log_function(sentBytes)

    if received_data:
        log_function("")
        log_function("Received {} byte(s):".format(len(received_data)))
        log_function("")
        rcvdBytes = ""
        for byte in received_data:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)
        log_function(rcvdBytes)


def read(device, skip, receive_length, log_function):
    """
    Read data from connected 1Wire device
    """
    onewire_device = OneWireDevice(device.oneWire)

    command = "SELECT"
    if skip:
        command = "SKIP"

    try:
        received_data = onewire_device.read(receive_length, command)
    except BinhoException:
        log_function("1Wire read status: fail")
        return

    log_function("1Wire read status: success")

    if received_data:
        log_function("")
        log_function("Received {} byte(s):".format(len(received_data)))
        log_function("")
        rcvdBytes = ""
        for byte in received_data:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)
        log_function(rcvdBytes)


def write(device, skip, data, log_function):
    """
    Write data to connected 1Wire device
    """
    onewire_device = OneWireDevice(device.oneWire)

    command = "SELECT"
    if skip:
        command = "SKIP"

    try:
        onewire_device.write(data, command)
    except BinhoException:
        log_function("1Wire write status: fail")
        return

    log_function("1Wire write status: success")
    log_function("")
    log_function("Wrote {} byte(s):".format(len(data)))
    log_function("")
    sentBytes = ""
    for byte in data:
        sentBytes += "\t " + "0x{:02x}".format(byte)
    log_function(sentBytes)


if __name__ == "__main__":
    main()
