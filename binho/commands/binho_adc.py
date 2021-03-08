#!/usr/bin/env python3

from __future__ import print_function

import sys
import errno
import statistics
import serial

from binho.utils import log_silent, log_verbose, binhoArgumentParser
from binho.errors import DeviceNotFoundError, CapabilityError


def main():

    # Set up a simple argument parser.
    parser = binhoArgumentParser(description="utility for reading from Binho host adapter's ADC")
    parser.add_argument(
        "-f",
        "--format",
        dest="format",
        type=str,
        default="voltage",
        choices=["voltage", "raw"],
        help="Format to output in.\nVoltage string, or raw fraction returned by the ADC.",
    )
    parser.add_argument(
        "-s", "--samples", dest="sample_count", type=int, default=1, help="The number of samples to read. (default: 1)",
    )
    parser.add_argument("-n", "--iopin", default=0, help="Use the given IO pin number for the ADC input")

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

    except serial.SerialException:
        print(
            "The target Binho host adapter was found, but failed to connect because another application already has an\
             open connection to it."
        )
        print("Please close the connection in the other application and try again.")
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
        adcPin = {}

        if args.iopin:
            if args.iopin.isnumeric():
                adcPin = "IO" + str(args.iopin)
            else:
                adcPin = args.iopin.upper()
        else:
            adcPin = device.adc.getDefaultADCPin()

        if args.sample_count == 0:
            raise CapabilityError("Cannot take 0 samples! Samples must be >= 1.")
        if args.sample_count > 1:
            log_function("Taking {} samples...".format(args.sample_count))
        else:
            log_function("Taking {} sample...".format(args.sample_count))

        log_function("")

        samples = []

        for x in range(args.sample_count):

            if args.format == "voltage":

                sample = device.adc.readInputVoltage(adcPin)
                log_function("[{}] ADC channel {} reads {} Volts".format(x + 1, adcPin, sample))

            else:
                sample = device.adc.readInputRaw(adcPin)
                log_function("[{}] ADC channel {} reads {}".format(x + 1, adcPin, sample))

            samples.append(sample)

        log_function("")

        if args.format == "voltage":
            log_function(
                "Stats: Min = {} V, Mean = {} V, Max = {} V, Range = {} V (n = {})".format(
                    min(samples),
                    statistics.mean(samples),
                    max(samples),
                    "%.3f" % (max(samples) - min(samples)),
                    len(samples),
                )
            )
        else:
            log_function(
                "Stats: Min = {}, Mean = {}, Max = {}, Range = {} (n = {})".format(
                    min(samples),
                    statistics.mean(samples),
                    max(samples),
                    "%.3f" % (max(samples) - min(samples)),
                    len(samples),
                )
            )

    finally:
        # close the connection to the host adapter
        device.close()


if __name__ == "__main__":
    main()
