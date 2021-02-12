class binhoI2CDriver:
    def __init__(self, usb, i2cIndex=0):

        self.usb = usb
        self.i2cIndex = i2cIndex

    @property
    def clockFrequency(self):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " CLK ?")
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " CLK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-I2C' + str(self.i2cIndex) + ' CLK"'
            )

        return int(result[10:])

    @clockFrequency.setter
    def clockFrequency(self, clock):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " CLK " + str(clock))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(f'Error Binho responded with {result}, not the expected "-OK"')

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
            raise AttributeError("usePullups can be only be set to a value of True (1) or False (0), not " + str(pull))

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " PULL " + str(val))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    @property
    def addressBits(self):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " ADDR ?")
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " ADDR"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-I2C' + str(self.i2cIndex) + ' CLK"'
            )

        if "8BIT" in result:
            return 8
        if "7BIT" in result:
            return 7

        raise RuntimeError(
            f'Error Binho responded with {result}, not the expected "-I2C' + str(self.i2cIndex) + ' CLK"'
        )

    @addressBits.setter
    def addressBits(self, bits):

        if 7 <= bits <= 8:
            self.usb.sendCommand("I2C" + str(self.i2cIndex) + " ADDR " + str(bits))
            result = self.usb.readResponse()

            if not result.startswith("-OK"):
                raise RuntimeError(f'Error Binho responded with {result}, not the expected "-OK"')

            return True

        raise AttributeError("AddressBits can be only be set to a value of 7 or 8, not " + str(bits))

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
            raise RuntimeError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def writeByte(self, data):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " WRITE " + str(data))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def readByte(self, address):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " REQ " + str(address) + " 1")
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " RXD"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-I2C' + str(self.i2cIndex) + ' RXD"'
            )

        return chr(result[10:])

    def readBytes(self, address, numBytes):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " REQ " + str(address) + " " + str(numBytes))
        result = self.usb.readResponse()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " RXD"):
            raise RuntimeError(
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
                raise RuntimeError(f'Error Binho responded with {result}, not the expected "-OK"')

            return bytearray()

        if not result.startswith("-I2C" + str(self.i2cIndex) + " RXD "):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-I2C ' + str(self.i2cIndex) + ' RXD ..."'
            )

        return bytearray.fromhex(result[9:])

    def start(self, address):

        self.usb.sendCommand("I2C" + str(self.i2cIndex) + " START " + str(address))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(f'Error Binho responded with {result}, not the expected "-OK"')
        return True

    def end(self, repeat=False):

        if repeat:
            self.usb.sendCommand("I2C" + str(self.i2cIndex) + " END R")
        else:
            self.usb.sendCommand("I2C" + str(self.i2cIndex) + " END")

        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def setSlaveAddressI2C(self, i2cIndex, address):

        self.usb.sendCommand("I2C" + str(i2cIndex) + " SLAVE " + str(address))
        result = self.usb.readResponse()

        return result

    def getSlaveAddressI2C(self, i2cIndex):

        self.usb.sendCommand("I2C" + str(i2cIndex) + " SLAVE ?")
        result = self.usb.readResponse()

        return result

    def getSlaveRequestInterruptI2C(self, i2cIndex):

        result = self.usb.interruptCheck("!I2C" + str(i2cIndex) + " SLAVE RQ")

        return result

    def clearSlaveRequestInterruptI2C(self, i2cIndex):

        self.usb.interruptClear("!I2C" + str(i2cIndex) + " SLAVE RQ")

    def getSlaveReceiveInterruptI2C(self, i2cIndex):

        result = self.usb.interruptCheck("!I2C" + str(i2cIndex) + " SLAVE RX")

        return result

    def clearSlaveReceiveInterruptI2C(self, i2cIndex):

        self.usb.interruptClear("!I2C" + str(i2cIndex) + " SLAVE RX")

    def setSlaveRegisterI2C(self, i2cIndex, register, value):

        self.usb.sendCommand("I2C" + str(i2cIndex) + " SLAVE REG " + str(register) + " " + str(value))
        result = self.usb.readResponse()

        return result

    def getSlaveRegisterI2C(self, i2cIndex, register):

        self.usb.sendCommand("I2C" + str(i2cIndex) + " SLAVE REG " + str(register) + " ?")
        result = self.usb.readResponse()

        return result

    def setSlaveReadMaskI2C(self, i2cIndex, register, value):

        self.usb.sendCommand("I2C" + str(i2cIndex) + " SLAVE READMASK " + str(register) + " " + str(value))
        result = self.usb.readResponse()

        return result

    def getSlaveReadMaskI2C(self, i2cIndex, register):

        self.usb.sendCommand("I2C" + str(i2cIndex) + " SLAVE READMASK " + str(register) + " ?")
        result = self.usb.readResponse()

        return result

    def setSlaveWriteMaskI2C(self, i2cIndex, register, value):

        self.usb.sendCommand("I2C" + str(i2cIndex) + " SLAVE WRITEMASK " + str(register) + " " + str(value))
        result = self.usb.readResponse()

        return result

    def getSlaveWriteMaskI2C(self, i2cIndex, register):

        self.usb.sendCommand("I2C" + str(i2cIndex) + " SLAVE WRITEMASK " + str(register) + " ?")
        result = self.usb.readResponse()

        return result

    def setSlaveModeI2C(self, i2cIndex, mode):

        self.usb.sendCommand("I2C" + str(i2cIndex) + " SLAVE MODE " + str(mode))
        result = self.usb.readResponse()

        return result

    def getSlaveModeI2C(self, i2cIndex):

        self.usb.sendCommand("I2C" + str(i2cIndex) + " SLAVE MODE " + "?")
        result = self.usb.readResponse()

        return result

    def setSlaveRegisterCount(self, i2cIndex, registerCount):

        self.usb.sendCommand("I2C" + str(i2cIndex) + " SLAVE REGCNT " + str(registerCount))
        result = self.usb.readResponse()

        return result

    def getSlaveRegisterCount(self, i2cIndex):

        self.usb.sendCommand("I2C" + str(i2cIndex) + " SLAVE REGCNT " + "?")
        result = self.usb.readResponse()

        return result
