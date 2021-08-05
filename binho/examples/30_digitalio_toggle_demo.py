"""This example demonstrates how to use the digital IO pins on Nova to generate pulses of
a specied duration, as short as ~5microseconds, max of 256milliseconds."""


import sys

# import the binho library
from binho import binhoHostAdapter

# These imports help us handle errors gracefully
import errno
from serial import SerialException
from binho.errors import DeviceNotFoundError
from binho.interfaces.gpio import IOMode


# Included for demonstrating the various ways to find and connect to Binho host adapters
# be sure to change them to match you device ID / comport
targetComport = "COM3"
targetDeviceID = "0x1c4780b050515950362e3120ff141c2a"

# Start by finding the desired host adapter and connecting to it
# wrap this with try/except to elegantly capture any connection errors
try:

    # grab the first device found the system finds
    binho = binhoHostAdapter()

    # When working with multiple host adapters connected to the same system
    # you can use any of the following methods to connect:

    # 1) grab the device with a specific index
    # binho = binhoHostAdapter(index=0)

    # 2) or get the device using the COM port
    # binho = binhoHostAdapter(port=targetComport)

    # 3) or get the device using the deviceID number
    # binho = binhoHostAdapter(deviceID = targetDeviceID)

except SerialException:

    print(
        "The target Binho host adapter was found, but failed to connect because another application already has an open\
         connection to it.",
        file=sys.stderr,
    )
    print(
        "Please close the connection in the other application and try again.", file=sys.stderr,
    )
    sys.exit(errno.ENODEV)

except DeviceNotFoundError:

    print(
        "No Binho host adapter found on serial port '{}'.".format(targetComport), file=sys.stderr,
    )
    sys.exit(errno.ENODEV)


# Once we made it this for, the connection to the device is open.
# wrap this with try/except to elegantly capture any errors and manage closing the
# connection to the host adapter automatically
try:

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

    else:
        print("Connected to a {} (deviceID: {}) on {}".format(binho.productName, binho.deviceID, binho.commPort))

    # set the host adapter operationMode to 'IO'
    # binho.operationMode = "IO"

    print()

    # Pins are available directly on the adapter object
    ioPin = binho.IO4

    print()

    # For the rest of this example, we'll be using IO0 directly on the adapter.

    # set the pin to be a Digital OUTput
    binho.IO4.mode = IOMode.DOUT
    print("Pin Configured for {} mode".format(binho.IO4.mode))

    # use the value property to read the current state of the pin
    print("The value is now is {}.".format(binho.IO4.value))
    print()

    # send a positive pulse for 2.5ms (2500 microseconds)
    # this command is blocking, and will only return after the pulse has completed.
    binho.IO4.toggle(2500)
    print("Positive 2.5ms pulse Completed!")

    # drive the pin high
    binho.IO4.value = 1
    print("The value is now is {}.".format(binho.IO4.value))

    # send a negative pulse for 1ms (1000 microseconds)
    # this command is blocking, and will only return after the pulse has completed.
    binho.IO4.toggle(1000)
    print("Negative 1ms pulse Completed!")

    # providing a delay of 0 will result in a minimal delay, typically ~5microseconds.
    binho.IO4.toggle(0)
    print("Just sent a minimally-short negative pulse, ends up being ~5us when observed.")

    # the minimal value observed above can be subtracted out to get very precise
    # timing control
    binho.IO4.toggle(1000-5)
    print("This pulse will be even closer to 1ms")

    # The maximum supported pulse duration is 256milliseconds, durations above
    # this limit will raise an exception
    binho.IO4.toggle(256000)
    print("Negative 256ms pulse Completed!")

    print()

    # drive the pin low to end the demo
    binho.IO4.value = 0
    print("The value is now is {}.".format(binho.IO4.value))

    print("The demo is finished!")

finally:

    # close the connection to the host adapter
    binho.close()
