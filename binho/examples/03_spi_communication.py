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

    # set the host adapter operationMode to 'SPI'
    binho.operationMode = "SPI"

    # Let's explore which pins are available for use as CS pins
    # when we're in SPI mode
    pins = binho.gpio.getAvailablePins()
    print("List of available Pins:")

    for pin in pins:
        print(pin)

    print()

    # Let's grab the first available pin (IO0) to use as cs
    # look at the digitalIO example for more info about working with digital
    # IO pins
    csPinName = pins[0]
    csPin = binho.gpio.getPin(csPinName)

    # in some occasions, no CS pin is need, so you can set the pin to None
    # csPin = None

    # Additionally, most CS pins are active low, however if you want the CS pin
    # to operate as an active high signal, you can mark it as inverted
    # invertCS = True
    invertCS = True

    print("Default SPI bus configuration:")
    print(
        "Mode: {}, Clk Freq: {} Hz, Bit Order: {}, Bits per Transfer: {}".format(
            binho.spi.mode,
            binho.spi.frequency,
            binho.spi.bitOrder,
            binho.spi.bitsPerTransfer,
        )
    )
    print("CSPin: {}, Inverted: {}".format(csPin.pinName, str(invertCS)))
    print()

    # Now that the CSpin is all sorted out, let's get our SPI bus running
    # First we'll set the SPI mode (0, 1, 2, or 3)
    binho.spi.mode = 1

    # And then set the SPI clock frequency, in Hz (500K, 800K, 1M, 2M, 3M, 4M,
    # 6M, 8M, 12M, and 24M Hz)
    binho.spi.frequency = 6000000

    # Next set the bit order. The default is MSbit first, but some devices want LSbit first.
    # binho.spi.bitOrder = "MSB"
    binho.spi.bitOrder = "LSB"

    # The last setting defines the bits per transfer, which can be set to either 8 or 16
    # binho.spi.bitsPerTransfer = 8
    binho.spi.bitsPerTransfer = 16

    # Lets review the configuration before sending data
    print("New SPI bus configuration:")
    print(
        "Mode: {}, Clk Freq: {} Hz, Bit Order: {}, Bits per Transfer: {}".format(
            binho.spi.mode,
            binho.spi.frequency,
            binho.spi.bitOrder,
            binho.spi.bitsPerTransfer,
        )
    )
    print("CSPin: {}, Inverted: {}".format(csPin.pinName, str(invertCS)))
    print()

    # we're ready to communicate on the bus, lets create a list of 4 bytes to
    # write to the bus
    txData = [0xDE, 0xAD, 0xBE, 0xEF]

    # since SPI bus is full-duplex, it can receive data while sending, so we'll use the transfer
    # function like this to capture any data that was sent back to the host
    # adapter
    rxData = binho.spi.transfer(
        txData, 4, chip_select=csPin, invert_chip_select=invertCS
    )

    # A simple way to test this is to connect the SDI and SDO signals together to create a
    # loopback. This will allow us to see how data is received.
    print(rxData)
    print()

    # The data is a byte array, which is easy to work with programmatically, but if you'd like to
    # print it to the console in a more human-friendly format, try this
    rcvdBytes = "RxData:"
    for byte in rxData:
        rcvdBytes += "\t " + "0x{:02x}".format(byte)

    print(rcvdBytes)
    print()

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
