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
        self, board, name="i2c bus", buffer_size=1024, clock_frequency=400000, enable_pullups=False,
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
            raise ValueError("invalid receive length!")

        if receive_length > self.buffer_size:
            raise ValueError("Tried to receive more than the size of the receive buffer.")

        if address > 127 or address < 0:
            raise ValueError("Tried to transmit to an invalid I2C address!")

        result = []
        status = True
        try:
            result = self.api.writeToReadFrom(hex(address), True, receive_length, 0, None)
        except BaseException:
            status = False

        return result, status

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
            raise ValueError("Tried to transmit to an invalid I2C address!")

        data = bytes(data)

        writeSuccess = True
        try:
            self.api.writeToReadFrom(hex(address), True, 0, len(data), data)
        except BaseException:
            writeSuccess = False

        return writeSuccess

    def transfer(self, address, data, receive_length):

        data = bytes(data)

        result = []
        status = True
        try:
            result = self.api.writeToReadFrom(hex(address), True, receive_length, len(data), data)
        except BaseException:
            status = False

        return result, status

    def scan(self):

        responses = []

        for i in range(8, 120):
            result = self.api.scanAddress(i)

            if result:
                responses.append(i)

        return responses
