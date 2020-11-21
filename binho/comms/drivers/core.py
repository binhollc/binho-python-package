class binhoCoreDriver:
    def __init__(self, usb, coreIndex=0):

        self.usb = usb
        self.coreIndex = coreIndex

    @property
    def deviceID(self):

        self.usb._sendCommand("+ID")
        result = self.usb._readResponse()

        if not result.startswith("-ID"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-ID"'
            )
        else:
            return result[4:]

    @property
    def firmwareVersion(self):

        self.usb._sendCommand("+FWVER")
        result = self.usb._readResponse()

        if not result.startswith("-FWVER"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-FWVER"'
            )
        else:
            return result[7:]

    @property
    def hardwareVersion(self):

        self.usb._sendCommand("+HWVER")
        result = self.usb._readResponse()

        if not result.startswith("-HWVER"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-HWVER"'
            )
        else:
            return result[7:]

    @property
    def commandVersion(self):

        self.usb._sendCommand("+CMDVER")
        result = self.usb._readResponse()

        if not result.startswith("-CMDVER"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-CMDVER"'
            )
        else:
            return result[8:]

    def resetToBtldr(self):

        self.usb._sendCommand("+BTLDR")
        result = self.usb._readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )
        else:
            return True

    def reset(self):

        self.usb._sendCommand("+RESET")
        result = self.usb._readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )
        else:
            return True

    def ping(self):
        self.usb._sendCommand("+PING")
        result = self.usb._readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )
        else:
            return True

    @property
    def operationMode(self):
        self.usb._sendCommand("+MODE " + str(self.coreIndex) + " ?")
        result = self.usb._readResponse()

        if not result.startswith("-MODE"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-MODE"'
            )
        else:
            return result[8:]

    @operationMode.setter
    def operationMode(self, mode):
        self.usb._sendCommand("+MODE " + str(self.coreIndex) + " " + mode)
        result = self.usb._readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )

        return True

    @property
    def numericalBase(self):
        self.usb._sendCommand("+BASE ?")
        result = self.usb._readResponse()

        if not result.startswith("-BASE"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-BASE"'
            )
        else:
            return result[6:]

    @numericalBase.setter
    def numericalBase(self, base):
        self.usb._sendCommand("+BASE " + str(base))
        result = self.usb._readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )

        return True

    def setLEDRGB(self, red, green, blue):
        self.usb._sendCommand("+LED " + str(red) + " " + str(green) + " " + str(blue))
        result = self.usb._readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )

        return True

    def setLEDColor(self, color):
        self.usb._sendCommand("+LED " + color)
        result = self.usb._readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )

        return True
