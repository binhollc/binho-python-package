# pylint: disable=too-few-public-methods
class binhoInterface():
    """
    Generic base class for binho peripherals.
    """

    def __init__(self, device):
        """ Default peripheral initializer -- just stores a reference to the relevant Binho device. """

        self.device = device
# pylint: enable=too-few-public-methods