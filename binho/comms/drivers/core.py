class binhoCoreDriver:
    def __init__(self, usb, coreIndex=0):

        self.usb = usb
        self.coreIndex = coreIndex

    @property
    def deviceID(self):

        self.usb.sendCommand("+ID")
        result = self.usb.readResponse()

        if not result.startswith("-ID"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-ID"'
            )
        else:
            return result[4:]

    @property
    def firmwareVersion(self):

        self.usb.sendCommand("+FWVER")
        result = self.usb.readResponse()

        if not result.startswith("-FWVER"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-FWVER"'
            )
        else:
            return result[7:]

    @property
    def hardwareVersion(self):

        self.usb.sendCommand("+HWVER")
        result = self.usb.readResponse()

        if not result.startswith("-HWVER"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-HWVER"'
            )
        else:
            return result[7:]

    @property
    def commandVersion(self):

        self.usb.sendCommand("+CMDVER")
        result = self.usb.readResponse()

        if not result.startswith("-CMDVER"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-CMDVER"'
            )
        else:
            return result[8:]

    def resetToBtldr(self):

        self.usb.sendCommand("+BTLDR")
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )
        else:
            return True

    def reset(self):

        self.usb.sendCommand("+RESET")
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )
        else:
            return True

    def ping(self):
        self.usb.sendCommand("+PING")
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )
        else:
            return True

    @property
    def operationMode(self):
        self.usb.sendCommand("+MODE " + str(self.coreIndex) + " ?")
        result = self.usb.readResponse()

        if not result.startswith("-MODE"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-MODE"'
            )
        else:
            return result[8:]

    @operationMode.setter
    def operationMode(self, mode):
        self.usb.sendCommand("+MODE " + str(self.coreIndex) + " " + mode)
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )

        return True

    @property
    def numericalBase(self):
        self.usb.sendCommand("+BASE ?")
        result = self.usb.readResponse()

        if not result.startswith("-BASE"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-BASE"'
            )
        else:
            return result[6:]

    @numericalBase.setter
    def numericalBase(self, base):
        self.usb.sendCommand("+BASE " + str(base))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )

        return True

    def setLEDRGB(self, red, green, blue):
        self.usb.sendCommand("+LED " + str(red) + " " + str(green) + " " + str(blue))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )

        return True

    def setLEDColor(self, color):
        self.usb.sendCommand("+LED " + color)
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-OK"'
            )

        return True
