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
        "The target Binho host adapter was found, but failed to connect because another application already has an open connection to it.",
        file=sys.stderr,
    )
    print(
        "Please close the connection in the other application and try again.",
        file=sys.stderr,
    )
    sys.exit(errno.ENODEV)

except DeviceNotFoundError:

    print(
        "No Binho host adapter found on serial port '{}'.".format(targetComport),
        file=sys.stderr,
    )
    sys.exit(errno.ENODEV)


# Once we made it this for, the connection to the device is open.
# wrap this with try/except to elegantly capture any errors and manage closing the
# connection to the host adapter automatically
try:

    print(
        "Connected to a {} (deviceID: {}) on {}".format(
            binho.productName, binho.deviceID, binho.commPort
        )
    )

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

    # For the rest of this example, we'll be using IO1 for Analog output
    pinNumber = binho.gpio.getPinIndex(1)
    io1 = binho.gpio.getPin(pinNumber)

    # set the pin to be a Analog OUTput
    # Options are 'DIN' (default), 'DOUT', 'AIN', 'AOUT', and 'PWM'
    # note that not all pins support all modes
    # we'll cover AIN and AOUT in the next example
    io1.mode = "AOUT"
    print("Trying out {} mode".format(io1.mode))

    # use the value property to set the output voltage, valid range of 0 - 1024
    io1.value = 512
    print("The value of {} is {}.".format(io1.pinName, io1.value))

    # I'm going to hang on to the IO1 pin to generate an analog signal that we can measure
    # and we'll use IO0 to measure the signal. You should connect IO1 and IO0 to perform
    # this example
    pinNumber = binho.gpio.getPinIndex(0)
    io0 = binho.gpio.getPin(pinNumber)

    io0.mode = "AIN"
    print("Trying out {} mode".format(io0.mode))

    # taking an analog reading is as simple as reading the io0.value property
    print("The value of {} is {}.".format(io0.pinName, io0.value))

    # However, there's an even easier way which abstracts all the low level stuff away
    # and provides some additional helper functions. this is achieved by using the
    # binho.dac object

    # the first advantage of using this approach is that you don't have to figure out
    # which pins has the DAC capability
    dacPin = binho.dac.getDefaultDACPin()
    print("The default DAC pin on {} is {}".format(binho.productName, dacPin))

    # using the dac object, there are convenient functions to set the output using
    # raw counts or desired voltage
    counts = 512
    binho.dac.setOutputRaw(counts)
    print("DAC channel {} set to {}".format(pinNumber, counts))

    voltage = 1.25
    binho.dac.setOutputVoltage(voltage)
    print("DAC channel {} set to {} Volts".format(pinNumber, voltage))

    # just like the dac object, there's also an adc object to make analog readings
    # more convenient too
    adcPin = binho.adc.getDefaultADCPin()
    print("The default ADC pin on {} is {}".format(binho.productName, adcPin))

    # read the voltage
    reading = binho.adc.readInputVoltage(adcPin)
    print("ADC channel {} reads {} Volts".format(adcPin, reading))

    # read the raw ADC counts
    reading = binho.adc.readInputRaw(adcPin)
    print("ADC channel {} reads {} counts".format(adcPin, reading))

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
