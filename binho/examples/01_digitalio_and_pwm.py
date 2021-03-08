"""This example demonstrates how to connect to a Binho host adapter and control the LED, a very simple 'hello world'-
esque example. A great intro to using this python library in your own python scripts."""


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
    binho.operationMode = "IO"

    # Let's explore which pins are available
    pins = binho.gpio.getAvailablePins()
    print("List of available Pins:")

    for pin in pins:
        print(pin)

    print()

    # Pins are available directly on the adapter object - using getPin and
    # releasePin is deprecated.
    ioPin = binho.IO0

    # each pin has helpful tracking info, like name and number
    print("Pin Number: {}, Pin Name: {}".format(ioPin.pin_number, ioPin.pin_name))

    # If desired, one can also get pins by name. The following is equivalent:
    ioPin = binho.gpio_pins["IO0"]
    print("Pin Number: {}, Pin Name: {}".format(ioPin.pin_number, ioPin.pin_name))

    # TODO: do we need to support getting pin by number?

    print()

    # For the rest of this example, we'll be using IO0 directly on the adapter.

    # set the pin to be a Digital INput
    # Options are 'DIN' (default), 'DOUT', 'AIN', 'AOUT', and 'PWM'
    # note that not all pins support all modes
    # we'll cover AIN and AOUT in the next example
    binho.IO0.mode = "DIN"
    print("Trying out {} mode on pin {}.".format(binho.IO0.mode, binho.IO0.pin_name))

    # For a more explicit style, the IOMode enum can also be used:
    binho.IO0.mode = IOMode.DIN
    print(f"Still trying out {binho.IO0.mode} mode.")

    # use the value property to read the current state of the pin
    print("The value is now is {}.".format(binho.IO0.value))
    print()

    # that's all you need to know for digital input
    # now let's set it to be a digital output
    binho.IO0.mode = "DOUT"
    print("Trying out {} mode".format(binho.IO0.mode))

    # drive the pin high
    binho.IO0.value = 1
    print("The value is now is {}.".format(binho.IO0.value))

    # drive the pin low
    binho.IO0.value = 0
    print("The value is now is {}.".format(binho.IO0.value))

    # you can also use strings 'HIGH' and 'LOW' if you'd like
    binho.IO0.value = "HIGH"
    print("The value is now is {}.".format(binho.IO0.value))

    binho.IO0.value = "LOW"
    print("The value is now is {}.".format(binho.IO0.value))
    print()

    # You can even use True and False, too.
    binho.IO0.value = True
    print("The value is now {}.".format(binho.IO0.value))

    binho.IO0.value = False
    print("The value is now {}.".format(binho.IO0.value))
    print()

    # Finally, lets try out PWM. Note that not all pins support PWM
    binho.IO0.mode = "PWM"
    print("Trying out {} mode".format(binho.IO0.mode))

    # set the pwm frequency to 10kHz (valid range is 750 - 80000)
    binho.IO0.pwmFreq = 10000

    # now set the value of the pwm generator, valid range is 0 (off) - 1024
    # (fully high)
    binho.IO0.value = 512
    print("PWM output is now {} (pwmFreq = {}Hz).".format(binho.IO0.value, binho.IO0.pwmFreq))

    # for convenience, you can also set the duty cycle using percent
    binho.IO0.value = "50%"
    print("PWM output is now {} (pwmFreq = {}Hz).".format(binho.IO0.value, binho.IO0.pwmFreq))

    print("Finished!")

finally:

    # close the connection to the host adapter
    binho.close()
