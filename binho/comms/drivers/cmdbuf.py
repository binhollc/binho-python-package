from binho.errors import DeviceError


class binhoCmdBufferDriver:
    def __init__(self, usb):

        self.usb = usb

    def add(self, command):

        self.usb.sendCommand("CMDB" + " ADD " + command)
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def clear(self):

        self.usb.sendCommand("CMDB" + " CLEAR")
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def loop(self, num_times):

        self.usb.sendCommand("CMDB" + " LOOP " + str(num_times))
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def trigger(self, trigger_event):

        self.usb.sendCommand("CMDB" + " TRIGGER " + trigger_event)
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True

    def begin(self):

        self.usb.sendCommand("CMDB" + " BEGIN")
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

        return True
