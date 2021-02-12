from ..interface import binhoInterface


class OneWireBus(binhoInterface):
    """
    Class representing a Binho host adapter 1Wire bus.
    """

    # Short name for this type of interface.
    INTERFACE_SHORT_NAME = "1wire"

    def __init__(
        self, board, name="1wire bus", io_number=0, pullup=False, buffer_size=1024
    ):  # pylint: disable=too-many-arguments, unused-argument
        """
        Initialize a new 1Wire bus.

        Args:
            board               -- The Binho host adapter whose 1Wire bus we want to control.
            name                -- The display name for the given 1Wire bus.
            io_number           -- The IO pin number on Binho host adapter for the 1Wire bus.
            pullup              -- True to engage the internal pullup resistor.
            buffer_size         -- The size of the 1Wire receive buffer on the Binho host adapter.
        """

        super().__init__(board)

        # Store a reference to the parent board.
        self.api = board.apis.oneWire
        self.board = board

        # Store our limitations.
        self.buffer_size = buffer_size

        # Create a list that will store all connected devices.
        self.devices = []

        # Set up the SPI bus for communications.
        board.apis.core.operationMode = "1WIRE"

    def begin(self, iopin, pullup):

        self.api.begin(iopin, pullup)

    def search(self):

        self.api.search()
        return self.api.getAddress()

    def attach_device(self, device):
        """
        Attaches a given 1Wire device to this bus. Typically called
        by the 1Wire device as it is constructed.
        Arguments:
            device -- The device object to attach to the given bus.
        """

        self.devices.append(device)

    def read(self, length=1, command="NONE"):
        """
        Attaches a given 1Wire device to this bus. Typically called
        by the 1Wire device as it is constructed.
        Arguments:
            device -- The device object to attach to the given bus.
        """

        rxData = []
        status = True
        try:
            rxData = self.api.exchangeBytes(command, [], length)
        except BaseException:
            status = False

        return rxData, status

    def write(self, data, command="NONE"):

        status = "success"

        try:
            self.api.exchangeBytes(command, data, 0)
        except BaseException:
            status = "fail"

        return status

    def transfer(self, data, receive_length=0, command="NONE"):
        """
        Sends (and typically receives) data over the SPI bus.
        Args:
            data                 -- the data to be sent to the given device.
            receive_length       -- the total amount of data to be read. If longer
                    than the data length, the transmit will automatically be extended
                    with zeroes.
            chip_select          -- the GPIOPin object that will serve as the chip select
                    for this transaction, None to use the bus's default, or False to not set CS.
            deassert_chip_select -- if set, the chip-select line will be left low after
                    communicating; this allows this transcation to be continued in the future
            spi_mode             -- The SPI mode number [0-3] to use for the communication. Defaults to 0.
        """

        result = []
        status = "success"
        try:
            result = self.api.exchangeBytes(command, data, receive_length)
        except BaseException:
            status = "fail"

        return result, status
