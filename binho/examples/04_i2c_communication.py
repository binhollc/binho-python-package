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
        print("Connected to a {} (deviceID: {}) on {}".format(binho.productName, binho.deviceID, binho.commPort))

    # set the host adapter operationMode to 'I2C'
    binho.operationMode = "I2C"

    # Let's start by looking at the default I2C bus settings
    print("Default I2C bus configuration:")
    print("Clk Freq: {} Hz, Use Internal PullUps: {}".format(binho.i2c.frequency, binho.i2c.useInternalPullUps))
    print()

    # The clock frequency can be configured to our desired frequency as shown below
    # binho.i2c.frequency = 100000
    # binho.i2c.frequency = 400000
    binho.i2c.frequency = 1000000
    # binho.i2c.frequency = 3400000

    # The internal pullup resistors can be controlled as shown below
    # binho.i2c.useInternalPullUps = False
    binho.i2c.useInternalPullUps = True

    # Let's scan for a list of I2C peripheral devices on the bus and display the results.
    # You'll want to have at least 1 I2C device connected for this example
    scanResults = binho.i2c.scan()

    print("Found {} I2C devices on the bus:".format(len(scanResults)))
    print(scanResults)
    print()

    # Hint: If you want to print the device list to the console in a much more human-friendly format
    # you can do it this way:
    print("Found {} I2C devices on the bus, but displayed more conveniently:".format(len(scanResults)))
    print("[{}]".format(", ".join(hex(x) for x in scanResults)))
    print()

    # We need to have at least one device on the bus for the rest of the
    # example to be meaningful
    if len(scanResults) > 0:

        # lets target the first device that was found
        targetDeviceAddress = scanResults[0]

    else:

        raise RuntimeError("No I2C Devices found, please connect a device to run the rest of the example.")

    # We know there's a device on the bus if we made it this far
    # so let's try to do a simple read from the device

    # Read 2 bytes from the target i2c device. This function returns the read
    # data, and will raise an exception if the read did not succeed.

    rxData = []

    try:
        rxData = binho.i2c.read(targetDeviceAddress, 2)
        print(rxData)

    except BinhoException:
        print("I2C Read Transaction failed!")

    print()

    # The data is a byte array, which is easy to work with programmatically, but if you'd like to
    # print it to the console in a more human-friendly format, try this
    rcvdBytes = "Read {} byte(s):\t".format(len(rxData))
    for byte in rxData:
        rcvdBytes += "\t " + "0x{:02x}".format(byte)

    print(rcvdBytes)
    print()

    # Let's try writing a byte to the device. Data is passed to the function as a list, so even though
    # we're just writing one byte, we need it to be in this format
    writeData = [0xAA]

    # Perform the I2C write with this function. It will raise an exception if
    # the transaction does not succeed.
    try:
        binho.i2c.write(targetDeviceAddress, writeData)

    except BinhoException:
        print("I2C Write transaction failed!")

    else:
        sentBytes = "Wrote {} byte(s):".format(len(writeData))

        for byte in writeData:
            sentBytes += "\t " + "0x{:02x}".format(byte)

        print(sentBytes)

    print()

    # Of course, it's very common to write and read to the device within the same transaction - as in when performing
    # a read register action. To make this easy, we'll use the transfer
    # function
    writeData = [0x01]
    bytesToRead = 2

    # Just like the i2c.read function, this will return data and raise an
    # exception if the transaction fails.
    rxData = []

    try:
        rxData = binho.i2c.transfer(targetDeviceAddress, writeData, bytesToRead)

    except BinhoException:
        print("I2C Transfer Transaction failed!")

    else:
        print("I2C Transfer Succeeded: ")
        sentBytes = "Wrote {} byte(s):".format(len(writeData))

        for byte in writeData:
            sentBytes += "\t " + "0x{:02x}".format(byte)

        rcvdBytes = "Read {} byte(s):\t".format(len(rxData))
        for byte in rxData:
            rcvdBytes += "\t " + "0x{:02x}".format(byte)

        print(sentBytes)
        print(rcvdBytes)

    print()

    # the i2c.transfer function is very general and can be used for many different purposes, but for clarity purposes,
    # lets try it again using different variable names that make more sense
    # for ReadRegister & WriteRegister operations

    # ReadRegister operation -- presumes that registers are 8bits wide
    regNumber = 0x01
    registersToRead = 1

    try:
        rxData = binho.i2c.transfer(targetDeviceAddress, [regNumber], registersToRead)
        print("The value of register {} is {}".format(regNumber, rxData[0]))
    except BinhoException:
        print("ReadRegister failed!")

    # WriteRegister -- presumes that registers are 8bits wide
    regNumber = 0x01
    regValue = 0xAA

    try:
        rxData = binho.i2c.transfer(targetDeviceAddress, [regNumber, regValue], 0)
        print("Wrote {} to register {}.".format(regValue, regNumber))
    except BinhoException:
        print("WriteRegister failed!")

    print("Finished!")

finally:

    # close the connection to the host adapter
    binho.close()
