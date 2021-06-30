#!/usr/bin/env python3

from __future__ import print_function

import errno
import sys
import ast

import binho  # pylint: disable=unused-import
from binho import binhoHostAdapter  # pylint: disable=unused-import
from binho.utils import log_silent, log_verbose, binhoArgumentParser
from binho.interfaces.i2cDevice import I2CDevice
from binho.interfaces.i2cBus import I2CBus
from binho.errors import DeviceNotFoundError, BinhoException


def main():

    # Set up a simple argument parser.
    parser = binhoArgumentParser(description="Utility for I2C communication via Binho host adapter")
    parser.add_argument(
        "-u", "--pullup", action="store_true", help="Enable 2.2k pullup resistors (3.3V)",
    )
    parser.add_argument("-f", "--frequency", default=None, help="Set clock frequency")
    parser.add_argument(
        "-a", "--address", nargs=1, type=ast.literal_eval, help="7-bit address for communication over the I2C Bus",
    )
    parser.add_argument(
        "-r", "--read", default=0, help="Number of bytes expecting to receive from the I2C Bus",
    )
    parser.add_argument(
        "-w", "--write", nargs="*", type=ast.literal_eval, default=[], help="Bytes to send over the I2C Bus",
    )
    parser.add_argument("-z", "--scan", action="store_true", help="Scan all possible i2c addresses")
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

        device.operationMode = "I2C"

        if args.frequency:
            log_function("Setting I2C clock frequency to {}Hz".format(args.frequency))
            device.i2c.frequency = int(args.frequency)

        if args.pullup:
            log_function(
                "Engaging the internal 2.2kOhm PullUp resistors. (Pulled to 3.3V). Remove the '-u' flag to rely on "
                + "external resistors."
            )
            device.i2c.useInternalPullUps = True
        else:
            log_function(
                "Internal 2.2kOhm PullUp resistors are disengaged. Add the '-u' flag to engage the internal resistors."
            )
            device.i2c.useInternalPullUps = False

        if args.scan:
            if args.frequency:
                scan(device, args.pullup, [int(args.frequency)])
            else:
                scan(device, args.pullup, [100000, 400000, 1000000, 3200000])

        if args.write and args.read:
            transmit(device, args.address[0], args.write, int(args.read), log_function)
        elif args.write:
            write(device, args.address[0], args.write, log_function)
        elif args.read:
            read(device, args.address[0], int(args.read), log_function)
        else:
            if not args.scan:
                log_function(
                    "No transaction performed. Please specify data to write with '-w' or a number of bytes to read "
                    + "using '-r'."
                )
                log_function("You can type 'binho i2c --help' for more information.")

    finally:
        # close the connection to the host adapter
        device.close()


def transmit(device, address, data, receive_length, log_function):
    """
    Write data to connected I2C device and then read from it in a single transaction
    """

    i2c_device = I2CDevice(device.i2c, address)

    log_function("Writing to address %s" % hex(address))
    sentBytes = "W:"
    for byte in data:
        sentBytes += "\t " + "0x{:02x}".format(byte)
    log_function(sentBytes)

    try:
        received_data = i2c_device.transfer(data, receive_length)
    except BinhoException:
        log_function("I2C transmit success: False")
        return

    if received_data:

        log_function("Read {} bytes received from address {}:".format(len(received_data), hex(address)))

        rcvdBytes = "R"
        for byte in received_data:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)
        log_function(rcvdBytes)

    log_function("I2C transmit success: True")


def read(device, address, receive_length, log_function):
    """
    Read data from connected I2C device
    """

    i2c_device = I2CDevice(device.i2c, address)

    try:
        received_data = i2c_device.read(receive_length)
    except BinhoException:
        log_function("I2C read success: False")
        return

    if received_data:
        log_function("Reading {} bytes from address {}:".format(len(received_data), hex(address)))

        rcvdBytes = "R:"
        for byte in received_data:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)
        log_function(rcvdBytes)

    log_function("I2C read success: True")


def write(device, address, data, log_function):
    """
    Write data to connected I2C device
    """
    i2c_device = I2CDevice(device.i2c, address)
    log_function("Writing {} bytes to address {}:".format(len(data), hex(address)))

    sentBytes = "W:"
    for byte in data:
        sentBytes += "\t " + "0x{:02x}".format(byte)
    log_function(sentBytes)

    try:
        i2c_device.write(data)
    except BinhoException:
        log_function("I2C write success: False")
    else:
        log_function("I2C write success: True")


def scan(device, pullup, frequencies):
    """
    Scan for connected I2C devices
        Standard mode: 100kHz
        Fast mode: 400kHz
        Fast mode plus: 1MHz
        high speed mode: 3.2MHz
    """
    addr_info = {}

    for clkFreq in frequencies:
        i2c_bus = I2CBus(device, clock_frequency=clkFreq, enable_pullups=pullup)
        rw_responses = i2c_bus.scan()

        for address in rw_responses:

            if address in addr_info:
                addr_info[address].append(clkFreq)
            else:
                addr_info[address] = [clkFreq]

    i2c_bus = I2CBus(device, clock_frequency=400000, enable_pullups=pullup)

    # list output
    print("I2C Bus Scan Report: (Address, Clock Frequency)")

    if len(addr_info) == 0:
        print("No devices found!")
        return

    print("Discovered %s I2C devices" % len(addr_info))
    print()

    for address in addr_info: # pylint: disable=consider-using-dict-items
        for clkHz in addr_info[address]:
            print("%s @ %dkHz" % (hex(address), clkHz / 1000))

        print()

    print()


if __name__ == "__main__":
    main()
