#!/usr/bin/env python3

from __future__ import print_function

import errno
import sys

import serial
from binho.utils import log_silent, log_verbose, binhoArgumentParser
from binho.errors import DeviceNotFoundError, CapabilityError


def main():

    # Set up a simple argument parser.
    parser = binhoArgumentParser(description="utility for reading from Binho host adapter's ADC")
    parser.add_argument(
        "-f",
        "--frequency",
        default=None,
        help="Set PWM frequency from 750Hz to 80000Hz",
    )
    parser.add_argument("-n", "--iopin", default=0, help="Provide the IO pin to use for the pwm output")
    parser.add_argument(
        "value",
        metavar="[value]",
        help="The desired duty cycle or raw value to load into the pwm generator.",
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

    except serial.SerialException:
        print(
            "The target Binho host adapter was found, but failed to connect because another application already has an \
             open connection to it."
        )
        print("Please close the connection in the other application and try again.")
        sys.exit(errno.ENODEV)

    except DeviceNotFoundError:
        if args.serial:
            print(
                "No Binho host adapter found matching Device ID '{}'.".format(args.serial),
                file=sys.stderr,
            )
        else:
            print("No Binho host adapter found!", file=sys.stderr)
        sys.exit(errno.ENODEV)

    # if we fail before here, no connection to the device was opened yet.
    # however, if we fail after this point, we need to make sure we don't
    # leave the serial port open.

    try:

        device.operationMode = "IO"

        pin = {}

        if args.iopin:
            if args.iopin.isnumeric():
                pinStr = "IO" + str(args.iopin)
            else:
                pinStr = args.iopin.upper()
        else:
            pinStr = "IO0"

        # Will need to clean this up later to support other products
        # however, will need to do some plumbing to make that work, don't want it to delay the
        # initial release of this library
        if pinStr == "IO1":
            raise CapabilityError("PWM Functionality is not supported on IO1 - please choose another pin!")

        # get the desired pin
        pin = device.gpio_pins[pinStr]

        # set the pin mode
        pin.mode = "PWM"
        log_function("Configuring {} for PWM output".format(pinStr))

        if args.frequency:
            if args.frequency.isnumeric():

                targetFreq = int(args.frequency)
                if targetFreq < 750 or targetFreq > 80000:
                    raise CapabilityError(
                        "PWM Frequency must be a number from 750 to 80000 (Hz), not {}".format(args.frequency)
                    )

                pin.pwmFreq = targetFreq
                log_function("Setting PWM Frequency to {} Hz".format(args.frequency))
            else:
                raise CapabilityError(
                    "PWM Frequency must be a number from 750 to 80000 (Hz), not {}".format(args.frequency)
                )

        if args.value.isnumeric():

            if 0 <= int(args.value) <= 1024:

                pin.value = args.value
                log_function(
                    "Setting PWM output to {} (~{}% duty cycle)".format(
                        args.value, "%.1f" % (int(args.value) / 1024 * 100.0)
                    )
                )

            else:
                raise CapabilityError(
                    "PWM value must be a number from 0 to 1023 (or 0% to 100%), not {}".format(args.value)
                )

        elif "%" in args.value:

            dutyCycle = args.value.strip("%")

            if dutyCycle.isnumeric():

                convValue = float(dutyCycle) / 100.0 * 1024

                if 0 <= int(convValue) <= 1024:

                    pin.value = int(convValue)
                    log_function(
                        "Setting PWM output to {} (~{}% duty cycle)".format(
                            int(convValue), "%.1f" % (int(convValue) / 1024 * 100.0)
                        )
                    )

                else:
                    raise CapabilityError(
                        "PWM value must be a number from 0 to 1023 (or 0% to 100%), not {}%".format(dutyCycle)
                    )

            else:
                raise CapabilityError(
                    "PWM value must be a number from 0 to 1023 (or 0% to 100%), not {}".format(args.value)
                )

        else:
            raise CapabilityError(
                "PWM value must be a number from 0 to 1023 (or 0% to 100%), not {}".format(args.value)
            )

    finally:
        # close the connection to the host adapter
        device.close()


if __name__ == "__main__":
    main()
