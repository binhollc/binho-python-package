from binho.device import binhoAPI


class binhoInterface:
    """
    Generic base class for Binho peripherals.

    :ivar device: The device containing this peripheral.
    :type device: binhoAPI
    """

    device: binhoAPI

    def __init__(self, device: binhoAPI):
        """
        Default peripheral initializer.

        Just stores a reference to the relevant Binho device.
        """

        self.device = device
