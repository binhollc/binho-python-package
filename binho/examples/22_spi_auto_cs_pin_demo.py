"""This example demonstrates how to connect to a Binho host adapter and configure Nova to automatically
toggle the CS pin for precise/optimal timing of SPI transactions."""

import sys

# import the binho library
from binho import binhoHostAdapter

# These imports help us handle errors gracefully
import errno
from serial import SerialException
from binho.errors import DeviceNotFoundError


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
        "The target Binho host adapter was found, but failed to connect because another application already has an open"
         "connection to it.",
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

    # set the host adapter operationMode to 'SPI'
    binho.operationMode = "SPI"

    # This example is meant to demonstrate the new automatic CS pin control features
    # introduced with Nova firmware version 0.2.7. It will not work with earlier
    # versions of firmware. You can update your Nova using the 'binho dfu -l' command

    # If you're unfamilair with the SPI API usage, please see the 03_spi_communicatio.py
    # example script.

    binho.spi.mode = 0
    binho.spi.frequency = 6000000
    binho.spi.bitOrder = "MSB"
    binho.spi.bitsPerTransfer = 8

    # Lets review the configuration before sending data
    print("SPI bus configuration:")
    print(
        "Mode: {}, Clk Freq: {} Hz, Bit Order: {}, Bits per Transfer: {}".format(
            binho.spi.mode, binho.spi.frequency, binho.spi.bitOrder, binho.spi.bitsPerTransfer,
        )
    )

    # Let's configure the automatic CS functionality
    cs_pin = 0      # in SPI mode, IO0 or IO1 can be used as CS pins
    
    polarity = 0    # 0 = Active Low, 1 = Active High
    
    pre_delay = 200   # number of microseconds to wait after assertion of the CS pin before
                    # the first bit of the transfer is sent. minimum is approx 50us.
    
    post_delay = 750  # number of microseconds to wait after the last bit of the transfer 
                    # has been sent before de-asserting the CS pin. minimum is approx. 5us.

    # This function is used to send the configuration down to Nova.
    binho.spi.autoCSConfig(cs_pin, polarity, pre_delay, post_delay)

    # we're ready to communicate on the bus, lets create a list of 4 bytes to
    # write to the bus
    txData = [0xDE, 0xAD, 0xBE, 0xEF]

    # Now that Nova will automatically control the CS pin, we can simply pass the data
    # to send to the transfer function
    rxData = binho.spi.transfer(txData, 4)

    # The automatic control of the CS pin can also be turned off using the follwing:
    # binho.spi.autoCSDisable()

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

finally:

    # close the connection to the host adapter
    binho.close()
