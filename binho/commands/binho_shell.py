#!/usr/bin/env python
#
from __future__ import print_function

import re
import sys
import errno

from IPython.terminal.interactiveshell import TerminalInteractiveShell

from binho.utils import binhoArgumentParser
from binho.util.interactive import binhoShellMagics


def main():  # pylint: disable=too-many-statements

    # Set up a simple argument parser.
    parser = binhoArgumentParser(description="Convenience shell for working with Binho host adapters.")
    parser.add_argument(
        "-e",
        "--exec",
        metavar="code",
        type=str,
        help="Executes the provided code as though it were passed "
        + "to a Binho host adapter shell, and then terminates.",
        dest="code",
    )
    parser.add_argument(
        "-E",
        "--pre-exec",
        metavar="code",
        type=str,
        help="Executes the provided code as though it were passed "
        + "to a Binho host adapter shell, but does not explicitly terminate.",
        dest="prelude",
    )
    parser.add_argument(
        "-f", "--file", metavar="file", type=str, help="Executes the relevant file before starting the given shell.",
    )
    parser.add_argument(
        "-M",
        "--automagic",
        dest="automagic",
        action="store_true",
        help="Enable automagic, so lazy developers don't have to type %%.",
    )
    parser.add_argument(
        "-P",
        "--avoid-parens",
        dest="avoidparens",
        action="store_true",
        help="Enable full autocall, so bare methods are executed, rather than printed.",
    )
    parser.add_argument(
        "-A",
        "--autoreload",
        dest="autoreload",
        action="store_true",
        help="Attempts to reload python modules automatically as they change; so current objects import new \
              functionality. This may sometimes break your shell.",
    )
    parser.add_argument(
        "-S",
        "--singleton",
        dest="singleton",
        action="store_true",
        help="Connect via a singleton that persists across device reconnects. Note: device state is not preserved.",
    )

    args = parser.parse_args()

    if args.singleton:
        connect_function = parser.get_singleton_for_specified_device
    else:
        connect_function = parser.find_specified_device

    binho = connect_function()

    if binho.inBootloaderMode:
        print(
            "{} found on {}, but it cannot be used now because it's in DFU mode".format(
                binho.productName, binho.commPort
            )
        )
        sys.exit(errno.ENODEV)

    elif binho.inDAPLinkMode:
        print(
            "{} found on {}, but it cannot be used now because it's in DAPlink mode".format(
                binho.productName, binho.commPort
            )
        )
        print("Tip: Exit DAPLink mode using 'binho daplink -q' command")
        sys.exit(errno.ENODEV)

    # Break into IPython for the shell.
    if not args.code:
        print("Spawning an IPython shell for easy access to your Binho host adapter.")
        print("Like normal python, you can use help(object) to get help for that object.\n")

        print("Try help(binho.gpio) to see the documentation for the Binho host adapter GPIO;")
        print("try dir(binho) to see a list of properties on the Binho Host Adapter object, and")
        print("try binho.available_interfaces() and binho.available_programmers() to see")
        print("the interfaces you can work with, and the programmers you can create.\n")

        singleton_text = "singleton " if args.singleton else ""
        print("A Binho host adapter {}object has been created for you as 'binho'. Have fun!\n".format(singleton_text))

    # Create a new shell, and give it access to our created Binho object.
    shell = TerminalInteractiveShell()
    shell.push("binho")

    # Create nice aliases for our primary interfaces.
    # pylint: disable=unused-variable
    i2c = binho.i2c
    spi = binho.spi
    dac = binho.dac
    adc = binho.adc
    oneWire = binho.oneWire
    # uart = binho.uart
    gpio = binho.gpio
    # shell.push(('i2c', 'spi', 'adc', 'uart', 'gpio',))
    shell.push(("i2c", "spi", "gpio", "dac", "adc", "oneWire"))
    # pylint: enable=unused-variable

    # Make the autoreload extension available.
    shell.extension_manager.load_extension("autoreload")

    # Add our magic commands, to make execution more 'fun'.
    shell.register_magics(binhoShellMagics)

    # If the user has requested automagic, let them have their automagic.
    if args.automagic:
        shell.automagic = True

    # If we're in avoid parenthesis mode
    if args.avoidparens:
        shell.autocall = 2

    # If we're using autoreload, enable that.
    if args.autoreload:
        shell.run_cell("%autoreload 2")
        print("Heads up: you've enabled autoreload. Things make break in unexpected ways as your code changes.")
        print("You can fix this by adjusting your expectations regarding breakage.\n")

    # Handle any inline execution requested.
    if args.code or args.prelude:

        # Replace any ;'s with newlines, so we can execute more than one
        # statement.
        code = args.code or args.prelude
        code = re.sub(r";\s*", "\n", code)
        lines = code.split("\n")

        # If we're in execute-and-quit mode, do so.

        for line in lines:
            shell.run_cell(line, shell_futures=True)

        # If we're to exit after running the relevant code, do so.
        if args.code:
            sys.exit(0)

    # If we have a file to execute, execute it.
    if args.file:
        shell.safe_execfile_ipy(args.file, shell_futures=True, raise_exceptions=True)

    # Run the shell itself.
    shell.connect_function = connect_function
    shell.mainloop()

    # close the connection to the device
    binho.close()


if __name__ == "__main__":
    main()
