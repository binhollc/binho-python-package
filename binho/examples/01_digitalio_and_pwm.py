"""This example demonstrates how to connect to a Binho host adapter and control the LED, a very simple 'hello world'-
esque example. A great intro to using this python library in your own python scripts."""


import sys

# import the binho library
from binho import binhoHostAdapter

# These imports help us handle errors gracefully
import errno
from serial import SerialException
from binho.errors import DeviceNotFoundError
from binho.utils import binho_error_hander


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

    print("Connected to a {} (deviceID: {}) on {}".format(binho.productName, binho.deviceID, binho.commPort))

    # set the host adapter operationMode to 'IO'
    binho.operationMode = "IO"

    # Let's explore which pins are available
    pins = binho.gpio.getAvailablePins()
    print("List of available Pins:")

    for pin in pins:
        print(pin)

    print()

    # let's grab the name of the first available pin
    pinName = pins[0]

    # using the getPin() function to get the pin will mark the pin as used
    # meaning that it won't show up in getAvailablePins() list until it's
    # released
    ioPin = binho.gpio.getPin(pinName)

    # each pin has helpful tracking info, like name and number
    print("Pin Number: {}, Pin Name: {}".format(ioPin.pinNumber, ioPin.pinName))

    # let's release the pin so we can reuse it again later
    binho.gpio.releasePin(ioPin)

    # you can also grab a pin by using it's name hardcoded
    pinName = "IO1"
    pinNumber = binho.gpio.getPinIndex(pinName)
    ioPin = binho.gpio.getPin(pinNumber)
    print("Pin Number: {}, Pin Name: {}".format(ioPin.pinNumber, ioPin.pinName))

    # let's release the pin so we can reuse it again later
    binho.gpio.releasePin(ioPin)

    # and of course, you can also get a pin with it's pin number
    pinNumber = binho.gpio.getPinIndex(2)
    ioPin = binho.gpio.getPin(pinNumber)
    print("Pin Number: {}, Pin Name: {}".format(ioPin.pinNumber, ioPin.pinName))

    # let's release the pin so we can reuse it again later
    binho.gpio.releasePin(ioPin)

    print()

    # For the rest of this example, we'll be using IO0
    pinNumber = binho.gpio.getPinIndex(0)
    io0 = binho.gpio.getPin(pinNumber)

    # set the pin to be a Digital INput
    # Options are 'DIN' (default), 'DOUT', 'AIN', 'AOUT', and 'PWM'
    # note that not all pins support all modes
    # we'll cover AIN and AOUT in the next example
    io0.mode = "DIN"
    print("Trying out {} mode".format(io0.mode))

    # use the value property to read the current state of the pin
    print("The value of {} is {}.".format(io0.pinName, io0.value))
    print()

    # that's all you need to know for digital input
    # now let's set it to be a digital output
    io0.mode = "DOUT"
    print("Trying out {} mode".format(io0.mode))

    # drive the pin high
    io0.value = 1
    print("The value of {} is {}.".format(io0.pinName, io0.value))

    # drive the pin low
    io0.value = 0
    print("The value of {} is {}.".format(io0.pinName, io0.value))

    # you can also use strings 'HIGH' and 'LOW' if you'd like
    io0.value = "HIGH"
    print("The value of {} is {}.".format(io0.pinName, io0.value))

    io0.value = "LOW"
    print("The value of {} is {}.".format(io0.pinName, io0.value))
    print()

    # Finally, lets try out PWM. Note that not all pins support PWM
    io0.mode = "PWM"
    print("Trying out {} mode".format(io0.mode))

    # set the pwm frequency to 10kHz (valid range is 750 - 80000)
    io0.pwmFreq = 10000

    # now set the value of the pwm generator, valid range is 0 (off) - 1024
    # (fully high)
    io0.value = 512
    print("PWM output on {} is {} (pwmFreq = {}Hz).".format(io0.pinName, io0.value, io0.pwmFreq))

    # for convenience, you can also set the duty cycle using percent
    io0.value = "50%"
    print("PWM output on {} is {} (pwmFreq = {}Hz).".format(io0.pinName, io0.value, io0.pwmFreq))

    print("Finished!")


# It's generally bad practice to indiscriminately catch all exceptions, however the
# binho_error_handler() simply prints out all the debug info as the script terminates
# it does not try to continue execution under any circumstances
except Exception:

    # Catch any exception that was raised and display it
    binho_error_hander()

finally:

    # close the connection to the host adapter
    binho.close()
