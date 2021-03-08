"""This example demonstrates how to connect to a Binho host adapter and control the LED, a very simple 'hello world'-
esque example. A great intro to using this python library in your own python scripts."""


import sys

# import the binho library
from binho import binhoHostAdapter

# These imports help us handle errors gracefully
import errno
from serial import SerialException
from binho.errors import DeviceNotFoundError, BinhoException

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
        print("Connected to a {} (deviceID: {}) on {}".format(
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

    except BinhoException:

        print("No 1Wire device was found attached to {}. Please check your setup and try again!".format(ioPin))
        sys.exit(1)

    # You can continue searching over and over again until all devices have been found. The search loads the
    # address of the desired device into the internal address buffer. Subsequent communications will be targeted at
    # this device.

    # The oneWire object provides functions for read, write, and transfer (write then read in the same transaction)
    # of these functions takes an optional 'command' parameter. This can be used to indicate that the transaction begin
    # with a 'SKIP' command, a 'SELECT' command, or 'NONE' (default), for no
    # command at all.

    # Let's read 4 bytes from the targeted oneWire device found in the search we
    # already performed. This command returns the received data upon success,
    # and will raise an exception upon failure.
    rxData = []

    try:
        rxData = binho.oneWire.read(4)

    except BinhoException:
        print("1Wire Read Transaction failed!")

    else:
        print(rxData)

    print()

    # The data is a byte array, which is easy to work with programmatically, but if you'd like to
    # print it to the console in a more human-friendly format, try this
    rcvdBytes = "Read {} byte(s):\t".format(len(rxData))
    for byte in rxData:
        rcvdBytes += "\t " + "0x{:02x}".format(byte)

    print(rcvdBytes)
    print()

    # as mentioned above, we can also tell the host adapter to begin the
    # transaction with a 'SKIP' command
    rxData = binho.oneWire.read(4, "SKIP")

    # we can also use the write command in a similar fashion
    writeData = [0xDE, 0xAD, 0xBE, 0xEF]

    try:
        binho.oneWire.write(writeData, command="SKIP")

    except BinhoException:
        print("1Wire Write Transaction failed!")

    else:
        sentBytes = "Wrote {} byte(s):".format(len(writeData))

        for byte in writeData:
            sentBytes += "\t " + "0x{:02x}".format(byte)

        print(sentBytes)

    print()

    # The reality is though that in most cases, you'll need to write and read data in the same transactions, so for this
    # you'll find the transfer() function very useful. The following example demonstrates how to interact with a DS24B33
    # 1-Wire EEPROM

    # Read the first 4 bytes saved in the EEPROM (note that we can't just read, we need to send the READ command to the
    # device first
    # that's why the transfer() function is so handy for EEPROMs
    writeData = [0xF0, 0x00, 0x00]
    readCount = 4
    rxData = []

    try:
        rxData = binho.oneWire.transfer(writeData, readCount, command="SKIP")

    except BinhoException:
        print("1. Read Failed!")

    else:
        rcvdBytes = "Read from EEPROM - Resp: {} byte(s):\t".format(len(rxData))

        for byte in rxData:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)

        print(rcvdBytes)

    # Now let's write some data to the scratchpad
    eepromCommand = [0x0F, 0x00, 0x00]
    scratchpadData = [0xDE, 0xAD, 0xBE, 0xEF]
    rxData = []

    try:
        rxData = binho.oneWire.transfer(eepromCommand + scratchpadData, 0, command="SKIP")

    except BinhoException:
        print("2. Write to Scratchpad Failed!")

    else:
        rcvdBytes = "Write To Scratchpad - Resp: {} byte(s):\t".format(len(rxData))

        for byte in rxData:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)

        print(rcvdBytes)

    # Read back from the scratchpad
    eepromCommand = [0xAA]
    rxData = []

    try:
        rxData = binho.oneWire.transfer(eepromCommand, 7, command="SKIP")

    except BinhoException:
        print("3. Read from Scratchpad Failed!")

    else:
        rcvdBytes = "Read From Scratchpad - Resp: {} byte(s):\t".format(len(rxData))

        for byte in rxData:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)

        print(rcvdBytes)

    # We need to retransmit this checksum to confirm the data in the scratchpad is correct. See device Datasheet for
    # the details / explanation
    commitConf = rxData[0:3]

    # Send the Copy Scratchpad command to commit the data to the EEPROM
    eepromCommand = [0x55]
    rxData = []

    try:
        rxData = binho.oneWire.transfer(eepromCommand + list(commitConf), 7, command="SKIP")

    except BinhoException:
        print("4. Send Copy Scratchpad Command Failed!")

    else:
        rcvdBytes = "Copy Scratchpad - Resp: {} byte(s):\t".format(len(rxData))

        for byte in rxData:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)

        print(rcvdBytes)

    # Finally read back the newly written data from the EEPROM
    writeData = [0xF0, 0x00, 0x00]
    readCount = 4
    rxData = []

    try:
        rxData = binho.oneWire.transfer(writeData, readCount, command="SKIP")

    except BinhoException:
        print("5. Read Back From EEPROM Failed!")

    else:
        rcvdBytes = "Read from EEPROM - Resp: {} byte(s):\t".format(len(rxData))

        for byte in rxData:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)

        print(rcvdBytes)

    print()
    print("Finished!")

finally:

    # close the connection to the host adapter
    binho.close()
