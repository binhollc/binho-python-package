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

    # set the host adapter operationMode to '1WIRE'
    binho.operationMode = "1WIRE"

    # The first thing about using 1WIRE is to configure which IO pin to use it with
    # and if we want to engage the internal pullup resistor for it (on IO0 and
    # IO1)
    ioPin = "IO0"
    usePullUp = True

    # This command creates the 1WIRE host on the provided IO pin
    binho.oneWire.begin(ioPin, usePullUp)

    # The first operation usually performed on a 1WIRE bus is a search. This
    # will raise an exception if no device was found
    try:

        address = binho.oneWire.search()

        full_addr = "0x"
        for byte in address:
            full_addr += "{:02x}".format(byte)

        print("Search discovered device with address = {}".format(full_addr))

    except BaseException:

        print(
            "No 1Wire device was found attached to {}. Please check your setup and try again!".format(
                ioPin
            )
        )
        sys.exit(1)

    # You can continue searching over and over again until all devices have been found. The search loads the
    # address of the desired device into the internal address buffer. Subsequent communcations will be targeted at
    # this device.

    # The oneWire object provides functions for read, write, and transfer (write then read in the same transaction)
    # of these functions takes an optional 'command' parameter. This can be used to indicate that the transaction begin
    # with a 'SKIP' command, a 'SELECT' command, or 'NONE' (default), for no
    # command at all.

    # Let's read 4 bytes from the targeted oneWire device found in the search we already performed. This command returns
    # a tuple so that we can check the status to know if the rxData is valid
    rxData, result = binho.oneWire.read(4)

    if result:
        print(rxData)
    else:
        print("1Wire Read Transaction failed!")

    print()

    # The data is a byte array, which is easy to work with programmatically, but if you'd like to
    # print it to the console in a more human-friendly format, try this
    rcvdBytes = "Read {} byte(s):\t".format(len(rxData))
    for byte in rxData:
        rcvdBytes += "\t " + "0x{:02x}".format(byte)

    print(rcvdBytes)
    print()

    # as mentioned above, we can also tell the host adapter to begin the
    # transaction with a 'SKIP' commmand
    rxData, status = binho.oneWire.read(4, "SKIP")

    # we can also use the write command in a similar fashion
    writeData = [0xDE, 0xAD, 0xBE, 0xEF]
    status = binho.oneWire.write(writeData, command="SKIP")

    if status:

        sentBytes = "Wrote {} byte(s):".format(len(writeData))

        for byte in writeData:
            sentBytes += "\t " + "0x{:02x}".format(byte)

        print(sentBytes)

    else:

        print("1Wire Write Transaction failed!")

    print()

    # The reality is though that in most cases, you'll need to write and read data in the same transactions, so for this
    # you'll find the transfer() function very useful. The following example demonstrates how to interact with a DS24B33
    # 1-Wire EEPROM

    # Read the first 4 bytes saved in the EEPROM (note that we can't just read, we need to send the READ command to the device first
    # that's why the transfer() function is so handy for EEPROMs
    writeData = [0xF0, 0x00, 0x00]
    readCount = 4
    rxData, status = binho.oneWire.transfer(writeData, readCount, command="SKIP")

    if status:
        rcvdBytes = "Read from EEPROM - Response: {} byte(s):\t".format(len(rxData))
        for byte in rxData:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)

        print(rcvdBytes)
    else:
        print("1. Read Failed!")

    # Now let's write some data to the scratchpad
    eepromCommand = [0x0F, 0x00, 0x00]
    scratchpadData = [0xDE, 0xAD, 0xBE, 0xEF]
    rxData, status = binho.oneWire.transfer(
        eepromCommand + scratchpadData, 0, command="SKIP"
    )

    if status:
        rcvdBytes = "Write To Scratchpad - Response: {} byte(s):\t".format(len(rxData))
        for byte in rxData:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)

        print(rcvdBytes)
    else:
        print("2. Write to ScratchPad Failed!")

    # Read back from the scratchpad
    eepromCommand = [0xAA]
    rxData, status = binho.oneWire.transfer(eepromCommand, 7, command="SKIP")

    if status:
        rcvdBytes = "Read From Scratchpad - Response: {} byte(s):\t".format(len(rxData))
        for byte in rxData:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)

        print(rcvdBytes)
    else:
        print("3. Read from ScratcPad Failed!")

    # We need to retransmit this checksum to confirm the data in the scratchpad is correct. See device Datasheet for
    # the details / explanation
    commitConf = rxData[0:3]

    # Send the Copy Scratchpad command to commit the data to the EEPROM
    eepromCommand = [0x55]
    rxData, status = binho.oneWire.transfer(
        eepromCommand + list(commitConf), 7, command="SKIP"
    )

    if status:
        rcvdBytes = "Copy Scratchpad - Response: {} byte(s):\t".format(len(rxData))
        for byte in rxData:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)

        print(rcvdBytes)
    else:
        print("4. Send Copy ScratcPad Command Failed!")

    # Finally read back the newly written data from the EEPROM
    writeData = [0xF0, 0x00, 0x00]
    readCount = 4
    rxData, status = binho.oneWire.transfer(writeData, readCount, command="SKIP")

    if status:
        rcvdBytes = "Read from EEPROM - Response: {} byte(s):\t".format(len(rxData))
        for byte in rxData:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)

        print(rcvdBytes)
    else:
        print("5. Read Back From EEPROM Failed!")

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
