from binho.errors import CapabilityError, DeviceError


class binho1WireDriver:
    def __init__(self, usb):
        self.usb = usb

    def begin(self, pin=0, pullup=False, oneWireIndex=0):
        """
        This function starts the 1-WIRE Master on the given IO pin. The 1-Wire protocol can be used
        on any of the IO pins, however it is especially convenient to use it on IO0 and IO2 as the
        internal pull-up resistor can be used thus eliminating the need for an external pull-up resistor.
        :param pin: The binho pin to use for 1-Wire comms can be 0-4
        :type pin: int
        :param pullup: True or False, enable the pullup on the IO pin
        :type pullup: bool
        :param oneWireIndex: The 1-Wire index, 0 on the binho nova
        :type oneWireIndex: int
        :raises DeviceError: if the command is unsuccessful
        :return: None
        :rtype: None
        """

        if pullup:
            self.usb.sendCommand(f"1WIRE{oneWireIndex} BEGIN {pin} PULL")
        else:
            self.usb.sendCommand(f"1WIRE{oneWireIndex} BEGIN {pin}")

        if not self.usb.checkDeviceSuccess(self.usb.readResponse()):
            raise DeviceError("Error executing 1-Wire Begin received NAK")

    def reset(self, oneWireIndex=0):
        """
        Send a 1-Wire reset pulse, return True if the binho receives a
        presence pulse False otherwise
        :param oneWireIndex: The 1-Wire index, 0 on the binho nova
        :type oneWireIndex: int
        :return: True if the binho receives a presence pulse False otherwise
        :rtype: bool
        """

        self.usb.sendCommand(f"1WIRE{oneWireIndex} RESET")

        return self.usb.checkDeviceSuccess(self.usb.readResponse())

    def writeByte(self, data, oneWireIndex=0, powered=True):
        """
        Write a byte over 1-Wire
        :param data: Data byte to write
        :type data: int
        :param oneWireIndex: The 1-Wire index, 0 on the binho nova
        :type oneWireIndex: int
        :param powered: Leave 1-Wire power on after this command finsihes
        :type powered: bool
        :raises DeviceError: if the command is unsuccessful
        :return: None
        :rtype: None
        """

        if not 0 <= data <= 255:
            raise CapabilityError(f"Data byte must be in range 0-255, not {data}")

        if powered:
            self.usb.sendCommand(f"1WIRE{oneWireIndex} WRITE {data} POWER")
        else:
            self.usb.sendCommand(f"1WIRE{oneWireIndex} WRITE {data}")

        if not self.usb.checkDeviceSuccess(self.usb.readResponse()):
            raise DeviceError("Error executing 1-Wire Write received NAK")

    def readByte(self, oneWireIndex=0):
        """
        Reads one byte over 1-Wire
        :param oneWireIndex: The 1-Wire index, 0 on the binho nova
        :type oneWireIndex: int
        :raises DeviceError: if the command is unsuccessful
        :return: Received byte
        :rtype: int
        """
        self.usb.sendCommand(f"1WIRE{oneWireIndex} READ")
        result = self.usb.readResponse()

        if result == "-NG":
            raise DeviceError("Error executing 1-Wire Read received NAK")

        return int(result[15:], 16)

    def exchangeBytes(self, oneWireCmd, bytesToWrite=None, bytesToRead=0, oneWireIndex=0):
        """
        Issues one of the following commands to the one wire bus:
            None (this is the default)
            Reset then Select ROM (requires a one wire address in the address buffer)
            Reset then Skip ROM
        Then writes bytesToWrite (max 1024) out to the bus
        Then reads bytesToRead (max 1024) from the bus
        :param oneWireCmd: 1-Wire command to send out on the bus
        :type oneWireCmd: oneWireCmd
        :param bytesToWrite: bytearray of bytes to write out to the 1-Wire bus after the 1-Wire Cmd
        :type bytesToWrite: bytearray
        :param bytesToRead: Number of bytes to read after writeing bytes
        :type bytesToRead: int
        :param oneWireIndex: The 1-Wire index, 0 on the binho nova
        :type oneWireIndex: int
        :return: A bytearray of bytes that were read out
        :rtype: bytearray
        """

        if len(bytesToWrite) > 1024:
            raise CapabilityError("WHR command can only write 1024 bytes at a time!")

        if bytesToRead > 1024:
            raise CapabilityError("WHR command can only read 1024 bytes at a time!")

        self.usb.sendCommand(
            f"1WIRE{oneWireIndex} "
            f"WHR {oneWireCmd} "
            f"{bytesToRead} "
            f"{len(bytesToWrite)} "
            f'{"".join(f"{b:02x}" for b in bytesToWrite)}'
        )

        result = self.usb.readResponse()

        if bytesToRead == 0:
            if not result.startswith("-OK"):
                raise DeviceError(f'Error Binho responded with {result}, not the expected "-OK"')

            return bytearray()

        if not result.startswith("-1WIRE0 RXD "):
            raise DeviceError(f'Error Binho responded with {result}, not the expected "-1WIRE0 RXD ..."')

        return bytearray.fromhex(result[12:])

    def select(self, oneWireIndex=0):
        """
        Select the device that was found as a result of the most recent SEARCH command
        :param oneWireIndex: The 1-Wire index, 0 on the binho nova
        :type oneWireIndex: int
        :raises DeviceError: if the command is unsuccessful
        :return: None
        :rtype: None
        """
        self.usb.sendCommand(f"1WIRE{oneWireIndex} SELECT")

        if not self.usb.checkDeviceSuccess(self.usb.readResponse()):
            raise DeviceError("Error executing 1-Wire Select received NAK")

    def skip(self, oneWireIndex=0):
        """
        Skip the device selection process, if there is one device on the bus
        :param oneWireIndex: The 1-Wire index, 0 on the binho nova
        :type oneWireIndex: int
        :raises DeviceError: if the command is unsuccessful
        :return: None
        :rtype: None
        """
        self.usb.sendCommand(f"1WIRE{oneWireIndex} SKIP")

        if not self.usb.checkDeviceSuccess(self.usb.readResponse()):
            raise DeviceError("Error executing 1-Wire Skip received NAK")

    def depower(self, oneWireIndex=0):
        """
        Power down the 1-WIRE bus
        :param oneWireIndex: The 1-Wire index, 0 on the binho nova
        :type oneWireIndex: int
        :raises DeviceError: if the command is unsuccessful
        :return: None
        :rtype: None
        """
        self.usb.sendCommand(f"1WIRE{oneWireIndex} DEPOWER")

        if not self.usb.checkDeviceSuccess(self.usb.readResponse()):
            raise DeviceError("Error executing 1-Wire depower received NAK")

    def getAddress(self, oneWireIndex=0):
        """
        Returns the address that was found by performing a 1-Wire search
        :param oneWireIndex: The 1-Wire index, 0 on the binho nova
        :type oneWireIndex: int
        :raises DeviceError: if the command is unsuccessful
        :return: Bytearray of the address
        :rtype: bytearray
        """
        self.usb.sendCommand(f"1WIRE{oneWireIndex} ADDR ?")
        result = self.usb.readResponse()

        if result == "-NG":
            raise DeviceError("Error executing 1-Wire Read received NAK")

        return bytearray.fromhex(result[13:].replace("0x", ""))

    def search(self, oneWireIndex=0, normalSearch=True):
        """
        Begin the process of searching for devices on the 1-WIRE bus.
        The address of the found device will be stored in internal address buffer
        :param oneWireIndex: The 1-Wire index, 0 on the binho nova
        :type oneWireIndex: int
        :param normalSearch: Whether to perform a normal search (returning all devices)
                                or only return alarming devices
        :type normalSearch: bool
        :raises DeviceError: if the command is unsuccessful
        :return: None
        :rtype: None
        """
        if normalSearch:
            self.usb.sendCommand(f"1WIRE{oneWireIndex} SEARCH")
        else:
            self.usb.sendCommand(f"1WIRE{oneWireIndex} SEARCH COND")

        if not self.usb.checkDeviceSuccess(self.usb.readResponse()):
            raise DeviceError("Error executing 1-Wire search received NAK")

    def resetSearch(self, oneWireIndex=0):
        """
        Resets 1-Wire search so a new one can occur
        :param oneWireIndex: The 1-Wire index, 0 on the binho nova
        :type oneWireIndex: int
        :raises DeviceError: if the command is unsuccessful
        :return: None
        :rtype: None
        """
        self.usb.sendCommand(f"1WIRE{oneWireIndex} SEARCH RESET")

        if not self.usb.checkDeviceSuccess(self.usb.readResponse()):
            raise DeviceError("Error executing 1-Wire search reset received NAK")

    def targetSearch(self, target, oneWireIndex=0):
        """
        Searches the 1-WIRE bus for devices belonging to a specific family code
        :param oneWireIndex: The 1-Wire index, 0 on the binho nova
        :type oneWireIndex: int
        :param target: 1-byte long device family code for which to search
        :type target: int
        :raises DeviceError: if the command is unsuccessful
        :return: None
        :rtype: None
        """
        if not 0 <= target <= 255:
            raise CapabilityError(f"Target byte must be in range 0-255, not {target}")

        self.usb.sendCommand(f"1WIRE{oneWireIndex} SEARCH {target}")

        if not self.usb.checkDeviceSuccess(self.usb.readResponse()):
            raise DeviceError("Error executing 1-Wire target search received NAK")
