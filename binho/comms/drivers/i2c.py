from binho.errors import CapabilityError, DeviceError


class binhoI2CDriver:
    def __init__(self, usb, i2cIndex=0):

        self.usb = usb
        self.i2cIndex = i2cIndex

    @property
    def clockFrequency(self):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " CLK ?")
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " CLK"):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-I2C' + str(self.i2cIndex) + ' CLK"'
            )

        return int(result[10:])

    @clockFrequency.setter
    def clockFrequency(self, clock):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " CLK " + str(clock))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    @property
    def usePullups(self):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " PULL ?")
        result = self.usb.readResponse()

        if "ENABLED" in result:
            return True

        return False

    @usePullups.setter
    def usePullups(self, pull):

        if pull or pull == 1:
            val = 1
        elif pull in (False, 0):
            val = 0
        else:
            raise CapabilityError("usePullups can be only be set to a value of True (1) or False (0), not " + str(pull))

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " PULL " + str(val))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    @property
    def addressBits(self):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " ADDR ?")
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " ADDR"):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-I2C' + str(self.i2cIndex) + ' CLK"'
            )

        if "8BIT" in result:
            return 8
        if "7BIT" in result:
            return 7

        raise DeviceError(
            f'Error Binho responded with {result}, not the expected "-I2C' + str(self.i2cIndex) + ' CLK"'
        )

    @addressBits.setter
    def addressBits(self, bits):

        if 7 <= bits <= 8:
            self.usb.sendCommand("I2C" + str(self.i2cIndex) + " ADDR " + str(bits))
            result = self.usb.readResponse()

            if not result.startswith("-OK"):
                raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

            return True

        raise CapabilityError("AddressBits can be only be set to a value of 7 or 8, not " + str(bits))

    def scanAddress(self, address, i2cIndex=0):

        self.usb.sendCommand("I2C" + str(i2cIndex) + " SCAN " + str(address))
        result = self.usb.readResponse()

        if "OK" in result:
            return True

        return False

    def write(self, address, startingRegister, data):

        dataPacket = ""

        for x in data:
            dataPacket += " " + str(x)

        self.usb.sendCommand(
            "I2C" + str(self.i2cIndex) + " WRITE " + str(address) + " " + str(startingRegister) + dataPacket
        )
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def writeByte(self, data):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " WRITE " + str(data))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def readByte(self, address):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " REQ " + str(address) + " 1")
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " RXD"):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-I2C' + str(self.i2cIndex) + ' RXD"'
            )

        return chr(result[10:])

    def readBytes(self, address, numBytes):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " REQ " + str(address) + " " + str(numBytes))
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " RXD"):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-I2C' + str(self.i2cIndex) + ' RXD"'
            )

        return bytearray.fromhex(result[10:])

    def writeToReadFrom(self, address, stop, numReadBytes, numWriteBytes, data):  # pylint: disable=too-many-arguments

        dataPacket = ""
        endStop = "1"

        if numWriteBytes > 0:
            for i in range(numWriteBytes):
                dataPacket += "{:02x}".format(data[i])
        else:
            dataPacket = "00"

        if not stop:
            endStop = "0"
        # print('I2C' + str(self.i2cIndex) + ' WHR ' + str(address) + ' ' + endStop + ' ' + str(numReadBytes) + ' ' \
        # + str(numWriteBytes) + ' ' + dataPacket)

        self.usb.sendCommand(
            "I2C"
            + str(self.i2cIndex)
            + " WHR "
            + str(address)
            + " "
            + endStop
            + " "
            + str(numReadBytes)
            + " "
            + str(numWriteBytes)
            + " "
            + dataPacket
        )
        result = self.usb.readResponse()

        # print(result)

        if numReadBytes == 0:
            if not result.startswith("-OK"):
                raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

            return bytearray()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " RXD "):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-I2C ' + str(self.i2cIndex) + ' RXD ..."'
            )

        return bytearray.fromhex(result[9:])

    def start(self, address):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " START " + str(address))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')
        return True

    def end(self, repeat=False):

        if repeat:
            self.usb.sendCommand("I2C" + str(self.i2cIndex) + " END R")
        else:
            self.usb.sendCommand("I2C" + str(self.i2cIndex) + " END")

        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def startPeripheralModeI2C(self, address, is_8bit = False):

        if is_8bit:
            address = address >> 1

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE " + str(address))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def inPeripheralModeI2C(self):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE ?")
        result = self.usb.readResponse()

        if result.startswith("-I2C" + str(self.i2cIndex) + " SLAVE "):

            if result.startswith("-I2C" + str(self.i2cIndex) + " SLAVE 0x00"):
                return False

            return True

        return False

    def getPeripheralAddressI2C(self):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE ?")
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " SLAVE "):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-I2C ' + str(self.i2cIndex) + ' SLAVE ..."'
            )

        return int(result[11:], 16)

    def getPeripheralRequestInterruptI2C(self):

        result = self.usb.interruptCheck("!I2C" + str(self.i2cIndex) + " SLAVE RQ")

        return result

    def clearPeripheralRequestInterruptI2C(self):

        self.usb.interruptClear("!I2C" + str(self.i2cIndex) + " SLAVE RQ")

    def getPeripheralReceiveInterruptI2C(self):

        result = self.usb.interruptCheck("!I2C" + str(self.i2cIndex) + " SLAVE RX")

        return result

    def clearPeripheralReceiveInterruptI2C(self):

        self.usb.interruptClear("!I2C" + str(self.i2cIndex) + " SLAVE RX")

    def setPeripheralRegisterValueI2C(self, register, value):

        print("I2C" + str(self.i2cIndex) + " SLAVE REG " + str(register) + " " + str(hex(value)))
        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE REG " + str(register) + " " + str(hex(value)))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            if register in ('PTR', 'ptr'):
                raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK". This could be caused' +
                                  ' by setting the pointer register to an index beyond the number of configured ' +
                                  'registers.')
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def getPeripheralRegisterValueI2C(self, register):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE REG " + str(register) + " ?")
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " SLAVE REG "):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-I2C' + str(self.i2cIndex) +
                ' SLAVE REG ..."'
            )

        return int(result[20:], 16)

    def setPeripheralRegisterReadMaskI2C(self, register, value):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE READMASK " + str(register) + " " + str(value))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def getPeripheralRegisterReadMaskI2C(self, register):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE READMASK " + str(register) + " ?")
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " SLAVE READMASK "):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-I2C ' + str(self.i2cIndex) +
                ' SLAVE READMASK ..."'
            )

        return int(result[26:], 16)

    def setPeripheralRegisterWriteMaskI2C(self, register, value):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE WRITEMASK " + str(register) + " " + str(value))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def getPeripheralRegisterWriteMaskI2C(self, register):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE WRITEMASK " + str(register) + " ?")
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " SLAVE WRITEMASK "):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-I2C ' + str(self.i2cIndex) +
                ' SLAVE WRITEMASK ..."'
            )

        return int(result[27:], 16)

    def setPeripheralModeI2C(self, mode):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE MODE " + str(mode))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def getPeripheralModeI2C(self):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE MODE " + "?")
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " SLAVE MODE "):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-I2C' + str(self.i2cIndex) + ' SLAVE MODE ..."'
            )

        return str(result[17:])

    def setPeripheralRegisterCountI2C(self, registerCount):

        if 0 < registerCount <= 256:

            self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE REGCNT " + str(registerCount))
            result = self.usb.readResponse()

            if not result.startswith("-OK"):
                raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

            return True

        raise CapabilityError("I2C Peripheral Register Count can only be set to a value between 1 " +
                              "and 256, not " + str(registerCount))


    def getPeripheralRegisterCountI2C(self):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE REGCNT " + "?")
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " SLAVE REGCNT "):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-I2C' + str(self.i2cIndex) +
                ' SLAVE REGCNT ..."' )

        return int(result[19:], 16)

    def getRegisterBankI2C(self):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE BANK " + "?")
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " SLAVE BANK "):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-I2C' + str(self.i2cIndex) + ' SLAVE BANK"'
            )

        return bytearray.fromhex(result[17:])

    def setRegisterBankI2C(self, data):

        payload = ""
        for _, val in enumerate(data):
            payload += "{:02x}".format(val)

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " SLAVE BANK " + str(payload))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True
        