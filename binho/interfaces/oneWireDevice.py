from ..interface import binhoInterface


class OneWireDevice(binhoInterface):
    """ Abstract base class representing a 1Wire-attached device. """

    def __init__(self, onewire_bus):
        """Sets up a new 1Wire-attached device.
        Parameters:
            onewire_bus     -- The 1Wire bus to which the given device is attached.
        """
        super().__init__(onewire_bus)
        # Store our interface...
        self._bus = onewire_bus

        # ... and register ourselves with the parent SPI bus.
        self._bus.attach_device(self)

    def transfer(self, data, read_length, command):
        """
        Sends (and typically receives) data over the SPI bus.
        Args:
            data                 -- the data to be sent to the given device.
            receive_length       -- the total amount of data to be read. If longer
                    than the data length, the transmit will automatically be extended
                    with zeroes.
            deassert_chip_select -- if set, the chip-select line will be left low after
                    communicating; this allows this transcation to be continued in the future
        """
        return self._bus.transfer(data, read_length, command)

    def write(self, data, command):
        """
        Sends (and typically receives) data over the SPI bus.
        Args:
            data                 -- the data to be sent to the given device.
            receive_length       -- the total amount of data to be read. If longer
                    than the data length, the transmit will automatically be extended
                    with zeroes.
            deassert_chip_select -- if set, the chip-select line will be left low after
                    communicating; this allows this transcation to be continued in the future
        """

        return self._bus.write(data, command)

    def read(self, length, command):
        """
        Sends (and typically receives) data over the SPI bus.
        Args:
            data                 -- the data to be sent to the given device.
            receive_length       -- the total amount of data to be read. If longer
                    than the data length, the transmit will automatically be extended
                    with zeroes.
            deassert_chip_select -- if set, the chip-select line will be left low after
                    communicating; this allows this transcation to be continued in the future
        """

        return self._bus.read(length, command)
