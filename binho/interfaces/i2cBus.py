from ..errors import CapabilityError
from ..interface import binhoInterface


class I2CBus(binhoInterface):
    """
    Class representing a Binho host adapter I2C bus.
    For now, supports only the primary I2C bus (I2C0), but will be
    expanded when the vendor commands are.
    """

    # Short name for this type of interface.
    INTERFACE_SHORT_NAME = "i2c"

    def __init__(
        self,
        board,
        name="i2c bus",
        buffer_size=1024,
        clock_frequency=400000,
        enable_pullups=False,
    ):  # pylint: disable=too-many-arguments, unused-argument
        """
        Initialize a new I2C bus.
        Args:
            board -- The Binho host adapter device whose I2C bus we want to control.
            name -- The display name for the given I2C bus.
            buffer_size -- The size of the I2C receive buffer on the Binho host adapter.
        """

        super().__init__(board)

        # Store a reference to the parent board, and our API.
        self.board = board
        self.api = board.apis.i2c

        # Store our limitations.
        self.buffer_size = buffer_size

        # Create a list that will store all connected devices.
        self.devices = []

        # Store the clock frequency & pullup config
        self.clock_frequency = clock_frequency
        self.enable_pullups = enable_pullups

        # Set up the I2C bus for communications.
        board.operationMode = "I2C"

        self.api.addressBits = 7

        # set the pullups
        self.useInternalPullUps = enable_pullups

        # set the clock frequency
        self.api.clockFrequency = clock_frequency

        # create the class to simplify control in I2C Peripheral mode
        self.peripheral = self.I2CPeripheral(self.api)

    def attach_device(self, device):
        """
        Attaches a given I2C device to this bus. Typically called
        by the I2C device as it is constructed.
        Arguments:
            device -- The device object to attach to the given bus.
        """

        # TODO: Check for address conflicts!

        self.devices.append(device)

    @property
    def frequency(self):
        return self.api.clockFrequency

    @frequency.setter
    def frequency(self, frequency):
        self.api.clockFrequency = frequency

    @property
    def useInternalPullUps(self):
        return self.api.usePullups

    @useInternalPullUps.setter
    def useInternalPullUps(self, enable):

        if enable:
            if not self.api.usePullups:
                self.api.usePullups = True
        else:
            self.api.usePullups = False

    def read(self, address, receive_length=0):
        """
        Reads data from the I2C bus.
        Args:
            address -- The 7-bit I2C address for the target device.
                Should not contain read/write bits. Can be used to address
                special addresses, for now; but this behavior may change.
            receive_length -- The I2C controller will attempt
                    to read the provided amount of data, in bytes.
        """

        if (not isinstance(receive_length, int)) or receive_length < 0:
            raise CapabilityError("invalid receive length!")

        if receive_length > self.buffer_size:
            raise CapabilityError("Tried to receive more than the size of the receive buffer.")

        if address > 127 or address < 0:
            raise CapabilityError("Tried to transmit to an invalid I2C address!")

        return self.api.writeToReadFrom(hex(address), True, receive_length, 0, None)

    def write(self, address, data):
        """
        Sends data over the I2C bus.
        Args:
            address -- The 7-bit I2C address for the target device.
                Should not contain read/write bits. Can be used to address
                special addresses, for now; but this behavior may change.
            data -- The data to be sent to the given device.
        """
        if address > 127 or address < 0:
            raise CapabilityError("Tried to transmit to an invalid I2C address!")
        self.api.writeToReadFrom(hex(address), True, 0, len(data), bytes(data))

    def transfer(self, address, data, receive_length):
        return self.api.writeToReadFrom(hex(address), True, receive_length, len(data), bytes(data))

    def scan(self):

        responses = []

        for i in range(8, 120):
            result = self.api.scanAddress(i)

            if result:
                responses.append(i)

        return responses

    class I2CPeripheral:

        def __init__(self, api):

            self.api = api

            self.registerBank = []

            for x in range(256):
                self.registerBank.append(self.I2CPeripheralRegister(self.api, x))

            self.pointerRegister = self.I2CPeripheralRegister(self.api, 'PTR', supports_permissions=False)

        @property
        def is_active(self):
            return self.api.inPeripheralModeI2C()

        @property
        def address(self):
            return self.api.getPeripheralAddressI2C()

        @property
        def mode(self):
            return self.api.getPeripheralModeI2C()

        @property
        def register_count(self):
            return self.api.getPeripheralRegisterCountI2C()

        @register_count.setter
        def register_count(self, count):
            if self.api.setPeripheralRegisterCountI2C(count):
                self.registerBank = []
                for x in range(count):
                    self.registerBank.append(self.I2CPeripheralRegister(self.api, x))
                return True
            return False


        def start(self, address, mode='USEPTR', is_8bit=False):
            if self.api.startPeripheralModeI2C(address, is_8bit):
                return self.api.setPeripheralModeI2C(mode)

            return False

        def readBank(self):
            return self.api.getRegisterBankI2C()

        def writeBank(self, data):
            return self.api.setRegisterBankI2C(data)

        class I2CPeripheralRegister:

            def __init__(self, api, number, supports_permissions=True):

                self.api = api
                self.permissions = supports_permissions
                self.register_number = number

            def __repr__(self):
                return str(hex(self.value))

            def configure(self, value, readMask=0xFF, writeMask=0xFF):

                if not self.api.setPeripheralRegisterValueI2C(self.register_number, value):
                    return False

                if self.permissions:

                    if not self.api.setPeripheralRegisterReadMaskI2C(self.register_number, readMask):
                        return False

                    if not self.api.setPeripheralRegisterWriteMaskI2C(self.register_number, writeMask):
                        return False

                return True

            @property
            def value(self):
                return self.api.getPeripheralRegisterValueI2C(self.register_number)

            @value.setter
            def value(self, value):
                return self.api.setPeripheralRegisterValueI2C(self.register_number, value)

            @property
            def readMask(self):
                if self.permissions:
                    return self.api.getPeripheralRegisterReadMaskI2C(self.register_number)

                return 0xFF

            @readMask.setter
            def readMask(self, readMask):
                if self.permissions:
                    return self.api.setPeripheralRegisterReadMaskI2C(self.register_number, readMask)

                return False

            @property
            def writeMask(self):
                if self.permissions:
                    return self.api.getPeripheralRegisterWriteMaskI2C(self.register_number)

                return 0xFF

            @writeMask.setter
            def writeMask(self, writeMask):
                if self.permissions:
                    return self.api.setPeripheralRegisterWriteMaskI2C(self.register_number, writeMask)

                return False
