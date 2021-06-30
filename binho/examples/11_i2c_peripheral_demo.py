from binho.interfaces.i2cDevice import I2CDevice
from binho.programmer import binhoProgrammer
import time
from math import log2, ceil, floor

import sys
from intelhex import IntelHex

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
        "The target Binho host adapter was found, but failed to connect because another application already has an open" +
         " connection to it.",
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

    # put the host adapter into I2C mode
    binho.operationMode = "I2C"

    # the I2C master is usually responsible for the pullups on the bus
    # but sometimes it's helpful to be able to use the pullups on the
    # Nova, so they are available in peripheral mode too
    binho.i2c.useInternalPullUps = True

    print('I2C Peripheral Mode Active: {}'.format(binho.i2c.peripheral.is_active))

    # Now start peripheral mode by providing the address and mode (mode='USEPTR' is the default)
    # binho.i2c.peripheral.start(0x70)
    # if you are more comfortable working with 8bit address, you can pass is_8bit=True as a
    # parameter and specify an 8bit value for the device address.
    binho.i2c.peripheral.start(0xE0, is_8bit=True)
    # The other mode is 'STARTZERO' -- see our support website for details
    # binho.i2c.peripheral.start(0x60, mode='STARTZERO')

    # These parameters can be checked later using the following read-only properties
    print('I2C Peripheral Active: {}'.format(binho.i2c.peripheral.is_active))
    print('I2C Peripheral Address: {}'.format(hex(binho.i2c.peripheral.address)))
    print('I2C Peripheral Mode: {}'.format(binho.i2c.peripheral.mode))

    # By default, the Nova emulates 256 x 8 bit registers, and all registers
    # are granted READ and WRITE permission. The default value of all
    # registers is 0xFF, and the Pointer Register is set to index 0.

    # The number of registers emulated in the memory bank can be changed
    # from 1 to 256, excluding the POINTER register. Let's set it to 8 registers.
    binho.i2c.peripheral.register_count = 8
    print('I2C Peripheral Register Count: {}'.format(binho.i2c.peripheral.register_count))

    # the registerBank automatically gets resized to match the register_count
    print('I2C Peripheral Register Bank Size: {}'.format(len(binho.i2c.peripheral.registerBank)))

    # The registers can be configured using the configure() function
    binho.i2c.peripheral.registerBank[0].configure(value=0xA0, readMask=0xFF, writeMask=0x00)

    # those values can be read back as well
    print("value = {}".format(hex(binho.i2c.peripheral.registerBank[0].value)))
    print("ReadMask = {}".format(hex(binho.i2c.peripheral.registerBank[0].readMask)))
    print("WriteMask = {}".format(hex(binho.i2c.peripheral.registerBank[0].writeMask)))

    # or by setting the value, readMask, and writeMask properties directly
    # let's make register 0 read-only:
    binho.i2c.peripheral.registerBank[0].value = 0xAA
    binho.i2c.peripheral.registerBank[0].readMask = 0xFF
    binho.i2c.peripheral.registerBank[0].writeMask = 0x00

    # let's make register 1 have 4 strobe (write-only) bits:
    binho.i2c.peripheral.registerBank[1].value = 0x0C
    binho.i2c.peripheral.registerBank[1].readMask = 0x0F
    binho.i2c.peripheral.registerBank[1].writeMask = 0xFF

    # it's possible to get the entire contents of the register bank as follows:
    print(binho.i2c.peripheral.registerBank)

    # The PTR register is used internally, but it can also be observed or modified
    # by the python script
    print("PTR value: {}".format(hex(binho.i2c.peripheral.pointerRegister.value)))

    # make sure that the pointerRegister always points to a valid register index.
    # The following assignment will raise an error if the value of the pointer register
    # exceeds the number of emulated registers.
    binho.i2c.peripheral.pointerRegister.value = 6
    print("PTR value: {}".format(hex(binho.i2c.peripheral.pointerRegister.value)))

    # To make things even faster, it's possible read/write the entire bank of registers
    # using a single function call. This reduces the amount of USB communication to a
    # single transaction for timing-critical applications.

    # let's read the entire bank of registers. The number of bytes returned is based on
    # the register_count configured above in line 116.
    regBankData = binho.i2c.peripheral.readBank()
    print(regBankData)

    # We can parse it to display it elegantly as such
    regBankvalues = ""
    for i in range(len(regBankData)):
        regBankvalues += "{:02x}".format(regBankData[i])

    print("Bank Value: 0x{}".format(regBankvalues))

    # we can modify the data and write it back to the device in a single transaction too.
    # note that the number of bytes being written must MATCH the register_count.
    regBankData[0] = 0xFF
    regBankData[7] = 0x88
    binho.i2c.peripheral.writeBank(regBankData)

    # read it back to verify it
    regBankData = binho.i2c.peripheral.readBank()
    print(regBankData)

    # and of course, we can create an entirely new bytearray and send it to the device
    # note that the number of bytes being written must MATCH the register_count.
    newBankData = [0xde, 0xad, 0xbe, 0xef, 0x01, 0x02, 0x03, 0x4]
    binho.i2c.peripheral.writeBank(bytearray(newBankData))

    # read it back to verify it
    regBankData = binho.i2c.peripheral.readBank()
    print(regBankData)

    # At this point, the Nova is behaving as configured on the I2C bus and will respond
    # accordingly to transactions with any I2C controller device that communicates with it
    print()
    print("Configuration Complete!")
    print("I2C Peripheral is active on Address {}".format(hex(binho.i2c.peripheral.address)))

finally:

    # close the connection to the host adapter
    binho.close()