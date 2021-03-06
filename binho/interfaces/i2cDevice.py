from ..errors import CapabilityError
from ..interface import binhoInterface


class I2CDevice(binhoInterface):
    """
    Class representing an generic I2C device connected to a Binho host adapter I2C Bus.
    This acts both as the base class for I2C devices, and as a generic class
    that can be used to access I2C devices for which no existing driver exists.
    """

    def __init__(self, bus, address, name="i2c device"):
        """
        Initialize a new generic I2C device.
        Args:
            bus -- An object representing the I2C bus on which this device
                resides.
            address - The address for the given I2C device on the bus.
            name -- The display name for the given I2C device.
        """
        super().__init__(bus)

        # Note: this will have to change if we decide to support 10-bit I2C
        # addresses.
        if address > 127 or address < 0:
            raise CapabilityError("Tried to attach a device to an unsupported I2C address.")

        # Store our device parameters.
        self.bus = bus
        self.address = address
        self.name = name

        # Attach our device to the parent bus.
        self.bus.attach_device(self)

    def transfer(self, data, receive_length):
        """
        Sends data over the I2C bus, and receives
        data in response.
        Args:
            data -- The data to be sent to the given device.
            receive_length -- If provided, the I2C controller will attempt
                    to read the provided amount of data, in bytes.
        """
        return self.bus.transfer(self.address, data, receive_length)

    def read(self, receive_length=0):
        """
        Reads data from the I2C bus.
        Args:
            receive_length -- The I2C controller will attempt
                    to read the provided amount of data, in bytes.
        """
        return self.bus.read(self.address, receive_length)

    def write(self, data):
        """
        Sends data over the I2C bus.
        Args:
            data -- The data to be sent to the given device.
        """
        return self.bus.write(self.address, data)
