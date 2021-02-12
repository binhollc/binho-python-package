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
# try:

ih = IntelHex()

# put the host adapter into I2C mode
binho.operationMode = "I2C"

# First thing we need to do is create the programmer object
# There are a number of common support devices which already have their parameters defined. You can use
# them by passing the part number in as show below:
programmer = binho.create_programmer("eeprom", device="24FC512")

# Alternatively, if the device is not built in, the EEPROM parameters needed can supplied as follows:
# eepromCapacityBytes = 65536         # capacity of EEPROM in Bytes
# eepromPageSizeBytes = 128           # EEPROM page size in Bytes
# eepromAddressOffset = 000           # Address offset determined by pins A0-A3, if present on package. Defaults to
#                                       0b000
# eepromWriteCycleTime = 0.005        # Time to wait for a write cycle, in
# seconds. Defaults to 5ms.

# The last parameter requires a bit of an explanation -- the bitmask indicates the meaning of the the 3 lowest address
#  bits
# eepromAddressBitmask = 'AAA'
# '0' or '1' = Bit is of fixed value
# 'A' = Bit is part of pin selectable slave address
# 'B' = Bit is part of block select address
# 'x' = Bit is a "don't care"

# And then pass all of those parameters in to create the programmer
# programmer = binho.create_programmer('eeprom', eepromCapacityBytes, eepromPageSizeBytes, bitmask=eepromAddressBitmask,
#              slave_address=eepromAddressOffset, write_cycle_length=eepromWriteCycleTime)

# If you want to use the on-board pullup resistors, engage them now
binho.i2c.useInternalPullUps = True

# It's possible to use the programmer to read and write bytes

# Reading 1024 bytes starting from address 0x00
data = programmer.readBytes(0x00, 1024)

# Writing 4 bytes starting at address 0x10
writeData = [0xDE, 0xAD, 0xBE, 0xEF]
programmer.writeBytes(0x10, writeData)


# However the key features of the programmer are for erase, read, write,
# and verify functionality

# Here's how easy it is to erase the memory, and then verify that it's blank
programmer.erase()
isBlank = programmer.blankCheck()
print("isBlank = {}".format(isBlank))

# Reading / Writing / Verifying EEPROMs from bin or hex files is also very
# easy:
dataFile = "testFile.bin"
programmer.writeFromFile("testFile2.bin", format="bin")
verifyResult = programmer.verifyFile("testFile2.bin", format="bin")

print("3. Verify bytearray")
ih.fromfile("testFile2-bad.bin", format="bin")
verData = ih.tobinarray()
verifyResult = programmer.verify(verData)
print("verification result: {}".format(verifyResult))

print("4. Verify File - binary")
verifyResult = programmer.verifyFile("testFile2-bad.bin", format="bin")
print("verification result: {}".format(verifyResult))

# programmer.writeFromFile('testFile2.bin', format='bin')
# programmer.readToFile('testFile-erasedFF.bin', format='bin')

# programmer.write(dataToWrite)


# Read All
# data = programmer.read()

# ih.frombytes(data)

# print('Min Addr: {}, Max Addr: {}'.format(str(ih.minaddr), str(ih.maxaddr)))
# ih.tofile("testFileErased-00.hex", format='hex')
# ih.tofile("testFileErased-00.bin", format='bin')

# writeData = [0xca, 0xfe, 0xbe, 0xef]

# programmer.write(writeData)

# print("Read {} Bytes, {} Kbits".format(len(data), len(data) * 8))


# It's generally bad practice to indiscriminately catch all exceptions, however the
# binho_error_handler() simply prints out all the debug info as the script terminates
# it does not try to continue execution under any circumstances
# except Exception:

# Catch any exception that was raised and display it
# binho_error_hander()

# finally:

# close the connection to the host adapter
binho.close()
