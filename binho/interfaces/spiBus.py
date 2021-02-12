from ..interface import binhoInterface


class SPIBus(binhoInterface):
    """
    Class representing a Binho host adapter SPI bus.
    For now, supports only the second SPI bus (SPI1), as the first controller
    is being used to control the onboard flash.
    """

    # Short name for this type of interface.
    INTERFACE_SHORT_NAME = "spi"

    def __init__(
        self, board, chip_select_gpio=None, name="spi bus", buffer_size=1024, clock_frequency=2000000,
    ):  # pylint: disable=too-many-arguments, unused-argument
        """
        Initialize a new SPI bus.

        Args:
            board               -- The Binho host adapter whose SPI bus we want to control.
            name                -- The display name for the given SPI bus.
            chip_select_gpio    -- The GPIOPin object that will represent the bus's default chip select
            buffer_size         -- The size of the SPI receive buffer on the Binho host adapter.
            clock_frequency     -- The frequency of the clock for the SPI bus.

        """
        super().__init__(board)

        # Store a reference to the parent board.
        self.api = board.apis.spi
        self.board = board

        # Store our limitations.
        self.buffer_size = buffer_size

        # Create a list that will store all connected devices.
        self.devices = []

        # Store our chip select.
        self._chip_select = chip_select_gpio

        # Set up the SPI bus for communications.
        board.operationMode = "SPI"

        self.api.clockFrequency = clock_frequency

        # Apply our frequency information.
        self.clock_frequency = clock_frequency

    def attach_device(self, device):
        """
        Attaches a given SPI device to this bus. Typically called
        by the SPI device as it is constructed.
        Arguments:
            device -- The device object to attach to the given bus.
        """

        # TODO: Check for select pin conflicts; and handle chip select pins.
        # TODO: replace the device list with a set of weak references

        self.devices.append(device)

    @property
    def mode(self):
        return self.api.mode

    @mode.setter
    def mode(self, mode):

        # changing the clock frequency will abort any transaction in progress
        self.api.end(True)
        self.api.mode = mode

    @property
    def frequency(self):
        return self.api.clockFrequency

    @frequency.setter
    def frequency(self, freq):

        # changing the clock frequency will abort any transaction in progress
        self.api.end(True)
        self.api.clockFrequency = freq

    @property
    def bitOrder(self):
        return self.api.bitOrder

    @bitOrder.setter
    def bitOrder(self, order):

        # changing the bitOrder will abort any transaction in progress
        self.api.end(True)
        self.api.bitOrder = order

    @property
    def bitsPerTransfer(self):
        return self.api.bitsPerTransfer

    @bitsPerTransfer.setter
    def bitsPerTransfer(self, bits):

        # changing the bitsPerTransfer will abort any transaction in progress
        self.api.end(True)
        self.api.bitsPerTransfer = bits

    def transfer(
        self,
        data,
        receive_length=None,
        chip_select=None,
        deassert_chip_select=True,
        spi_mode=0,
        invert_chip_select=False,
        frequency=None,
    ):  # pylint: disable=too-many-arguments, too-many-locals
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

        data_to_transmit = bytearray(data)
        data_received = bytearray()

        # If we weren't provided with a chip-select, use the bus's default.
        if chip_select is None:
            chip_select = self._chip_select

        if receive_length is None:
            receive_length = len(data)

        # If we need to receive more than we've transmitted, extend the data
        # out.
        if receive_length > len(data):
            padding = receive_length - len(data)
            data_to_transmit.extend([0] * padding)

        if spi_mode:
            # Set the polarity and phase (the "SPI mode").
            self.api.mode = spi_mode

        if frequency:
            self.api.clockFrequency = frequency

        self.api.begin()

        # Bring the relevant chip select low, to start the transaction.
        if chip_select:

            chip_select.mode = "DOUT"
            if invert_chip_select:
                chip_select.value = 1
            else:
                chip_select.value = 1
                chip_select.value = 0

        # Transmit our data in chunks of the buffer size.
        # Extract a single data chunk from the transmit buffer.
        chunk = data_to_transmit[0 : self.buffer_size]

        writeFlag = False
        if len(chunk) > 0:
            writeFlag = True

        readFlag = False
        if receive_length > 0:
            readFlag = True

        numBytes = len(chunk)
        if receive_length > numBytes:
            numBytes = receive_length

        # Finally, exchange the data.
        response = self.api.writeToReadFrom(writeFlag, readFlag, numBytes, bytes(chunk))
        data_received.extend(response)

        # Finally, unless the caller has requested we keep chip-select asserted,
        # finish the transaction by releasing chip select.
        if chip_select and deassert_chip_select:
            if invert_chip_select:
                chip_select.value = 0
            else:
                chip_select.value = 1

        self.api.end()

        # Once we're done, return the data received.

        return bytes(data_received)

    def disable_drive(self):
        """ Tristates each of the pins on the given SPI bus. """
        self.api.enable_drive(False)

    def enable_drive(self):
        """ Enables the bus to drive each of its output pins. """
        self.api.enable_drive(True)
