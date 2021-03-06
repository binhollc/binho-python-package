from binho.errors import DeviceError


class binhoSPIDriver:
    def __init__(self, usb, spiIndex=0):

        self.usb = usb
        self.spiIndex = spiIndex

    @property
    def clockFrequency(self):

        self.usb.sendCommand("SPI" + str(self.spiIndex) + " CLK ?")
        result = self.usb.readResponse()

        if not result.startswith("-SPI" + str(self.spiIndex) + " CLK"):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-SPI' + str(self.spiIndex) + ' CLK"'
            )

        return int(result[10:])

    @clockFrequency.setter
    def clockFrequency(self, clock):

        self.usb.sendCommand("SPI" + str(self.spiIndex) + " CLK " + str(clock))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    @property
    def bitOrder(self):

        self.usb.sendCommand("SPI" + str(self.spiIndex) + " ORDER ?")
        result = self.usb.readResponse()

        if not result.startswith("-SPI" + str(self.spiIndex) + " ORDER"):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-SPI' + str(self.spiIndex) + ' ORDER"'
            )

        return result[12:]

    @bitOrder.setter
    def bitOrder(self, order):

        self.usb.sendCommand("SPI" + str(self.spiIndex) + " ORDER " + order)
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    @property
    def mode(self):

        self.usb.sendCommand("SPI" + str(self.spiIndex) + " MODE ?")
        result = self.usb.readResponse()

        if not result.startswith("-SPI" + str(self.spiIndex) + " MODE"):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-SPI' + str(self.spiIndex) + ' MODE"'
            )

        return int(result[11:])

    @mode.setter
    def mode(self, mode):

        self.usb.sendCommand("SPI" + str(self.spiIndex) + " MODE " + str(mode))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    @property
    def bitsPerTransfer(self):

        self.usb.sendCommand("SPI" + str(self.spiIndex) + " TXBITS ?")
        result = self.usb.readResponse()

        if not result.startswith("-SPI" + str(self.spiIndex) + " TXBITS"):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-SPI' + str(self.spiIndex) + ' TXBITS"'
            )

        return int(result[13:])

    @bitsPerTransfer.setter
    def bitsPerTransfer(self, bits):

        self.usb.sendCommand("SPI" + str(self.spiIndex) + " TXBITS " + str(bits))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def begin(self):

        self.usb.sendCommand("SPI" + str(self.spiIndex) + " BEGIN")
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def transfer(self, data):

        self.usb.sendCommand("SPI" + str(self.spiIndex) + " TXRX " + str(data))
        result = self.usb.readResponse()

        if not result.startswith("-SPI" + str(self.spiIndex) + " RXD"):
            raise DeviceError(
                f'Error Binho responded with {result}, not the expected "-SPI' + str(self.spiIndex) + ' RXD"'
            )

        return bytearray.fromhex(result[9:])

    def writeToReadFrom(self, write, read, numBytes, data):

        dataPacket = ""
        writeOnlyFlag = "0"

        if write:
            if numBytes > 0:
                for i in range(numBytes):
                    dataPacket += "{:02x}".format(data[i])
            else:
                dataPacket = "0"
        else:
            # read only, keep writing the same value
            for i in range(numBytes):
                dataPacket += "{:02x}".format(data)

        if not read:
            writeOnlyFlag = "1"

        self.usb.sendCommand(
            "SPI" + str(self.spiIndex) + " WHR " + writeOnlyFlag + " " + str(numBytes) + " " + dataPacket
        )

        result = self.usb.readResponse()

        if not read:
            if not result.startswith("-OK"):
                raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

            return bytearray()

        if not result.startswith("-SPI0 RXD "):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-SPI0 RXD ..."')

        return bytearray.fromhex(result[9:])

    def end(self, suppressError=False):

        self.usb.sendCommand("SPI" + str(self.spiIndex) + " END")
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            if not suppressError:
                raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True
