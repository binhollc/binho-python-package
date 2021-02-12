class binhoIODriver:
    def __init__(self, usb, ioNumber):

        self.usb = usb
        self.ioNumber = ioNumber

    @property
    def mode(self):
        self.usb.sendCommand("IO" + str(self.ioNumber) + " MODE ?")
        result = self.usb.readResponse()

        if not result.startswith("-IO" + str(self.ioNumber) + " MODE"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-IO' + str(self.ioNumber) + ' MODE"'
            )

        return result[10:]

    @mode.setter
    def mode(self, mode):
        self.usb.sendCommand("IO" + str(self.ioNumber) + " MODE " + str(mode))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    @property
    def pwmFrequency(self):
        self.usb.sendCommand("IO" + str(self.ioNumber) + " PWMFREQ ?")
        result = self.usb.readResponse()

        if not result.startswith("-IO" + str(self.ioNumber) + " PWMFREQ"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-IO' + str(self.ioNumber) + ' PWMFREQ"'
            )

        return int(result[13:])

    @pwmFrequency.setter
    def pwmFrequency(self, freq):
        self.usb.sendCommand("IO" + str(self.ioNumber) + " PWMFREQ " + str(freq))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    @property
    def interruptSource(self):
        self.usb.sendCommand("IO" + str(self.ioNumber) + " INT ?")
        result = self.usb.readResponse()

        if not result.startswith("-IO" + str(self.ioNumber) + " INT"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-IO' + str(self.ioNumber) + ' INT"'
            )

        return result[8:]

    @interruptSource.setter
    def interruptSource(self, intMode):
        self.usb.sendCommand("IO" + str(self.ioNumber) + " INT " + intMode)
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    @property
    def value(self):
        self.usb.sendCommand("IO" + str(self.ioNumber) + " VALUE ?")
        result = self.usb.readResponse()

        if not result.startswith("-IO" + str(self.ioNumber) + " VALUE"):
            raise RuntimeError(
                f'Error Binho responded with {result}, not the expected "-IO' + str(self.ioNumber) + ' VALUE"'
            )

        if "%" in result or "V" in result:
            vals = result.split(" ")
            return int(vals[2])

        return int(result[11:])

    @value.setter
    def value(self, value):

        self.usb.sendCommand("IO" + str(self.ioNumber) + " VALUE " + str(value))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise RuntimeError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    @property
    def interruptFlag(self):
        result = self.usb.interruptCheck("!I0" + str(self.ioNumber))

        return result

    def clearInterrupt(self):
        self.usb.interruptClear("!IO" + str(self.ioNumber))
