from binho.errors import DeviceError


class binhoCoreDriver:
    def __init__(self, usb, coreIndex=0):

        self.usb = usb
        self.coreIndex = coreIndex

    @property
    def deviceID(self):

        self.usb.sendCommand("+ID")
        result = self.usb.readResponse()

        if not result.startswith("-ID"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-ID"')

        return result[4:]

    @property
    def firmwareVersion(self):

        self.usb.sendCommand("+FWVER")
        result = self.usb.readResponse()

        if not result.startswith("-FWVER"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-FWVER"')

        return result[7:]

    @property
    def hardwareVersion(self):

        self.usb.sendCommand("+HWVER")
        result = self.usb.readResponse()

        if not result.startswith("-HWVER"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-HWVER"')

        return result[7:]

    @property
    def commandVersion(self):

        self.usb.sendCommand("+CMDVER")
        result = self.usb.readResponse()

        if not result.startswith("-CMDVER"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-CMDVER"')

        return result[8:]

    def resetToBtldr(self, fail_silent=False):

        self.usb.sendCommand("+BTLDR")
        result = self.usb.readResponse()

        if not result.startswith("-OK") and not fail_silent:
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def reset(self):

        self.usb.sendCommand("+RESET")
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def ping(self):
        self.usb.sendCommand("+PING")
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    @property
    def operationMode(self):
        self.usb.sendCommand("+MODE " + str(self.coreIndex) + " ?")
        result = self.usb.readResponse()

        if not result.startswith("-MODE"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-MODE"')

        return result[8:]

    @operationMode.setter
    def operationMode(self, mode):
        self.usb.sendCommand("+MODE " + str(self.coreIndex) + " " + mode)
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    @property
    def numericalBase(self):
        self.usb.sendCommand("+BASE ?")
        result = self.usb.readResponse()

        if not result.startswith("-BASE"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-BASE"')

        return result[6:]

    @numericalBase.setter
    def numericalBase(self, base):
        self.usb.sendCommand("+BASE " + str(base))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def setLEDRGB(self, red, green, blue):
        self.usb.sendCommand("+LED " + str(red) + " " + str(green) + " " + str(blue))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def setLEDColor(self, color):
        self.usb.sendCommand("+LED " + color)
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True
