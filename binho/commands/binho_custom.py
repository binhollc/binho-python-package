#!/usr/bin/env python3

from __future__ import print_function

import sys
import errno
from binho.utils import log_silent, log_verbose, binhoArgumentParser
from binho.errors import DeviceNotFoundError

# this file is meant to serve as a template which can be used to create your own custom commands
# to be used in the Binho host adapter command line interface. Follow the naming convention of using the "binho_"
# prefix and the libraries will take care of everything else under the hood. You can also update the setup.py
# file in the root dir of the binho-python-package and add the following line to the console_scripts list:
#       'binho_custom = binho.commands.binho_custom:main'
# where [custom] is replaced with the name your custom command/file.


def main():

    # Set up a simple argument parser.
    parser = binhoArgumentParser(description="Sample template for creating custom Binho commands")
    parser.add_argument("-n", "--iopin", default=0, help="Get an IO pin from the command arguments")

    # run the argument parser
    args = parser.parse_args()

    # setup logging - this will be printed to the consoled if the '-v' flag
    # was passed as an argument
    log_function = log_verbose if args.verbose else log_silent

    # Now try to find the desired device based on the arguments
    # wrap this in a try/except trap to handle failures gracefully
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

    # use another try/except to elegantly deal with any errors in the custom
    # command logic, making sure the connection to the device is cleaned up
    try:

        # implement your custom command logic here
        # pylint: disable=unused-variable
        pin = {}

        if args.iopin:
            if args.iopin.isnumeric():
                pin = "IO" + str(args.iopin)
            else:
                pin = args.iopin.upper()
        else:
            pin = "IO0"
        # pylint: enable=unused-variable

        log_function("Taking {} samples...".format(args.sample_count))

    finally:
        # close the connection to the host adapter
        device.close()


# This is needed so that we can run sphinx to parse the code for in-line
# documentation
if __name__ == "__main__":
    main()
