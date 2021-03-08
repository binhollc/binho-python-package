class BinhoException(Exception):
    """
    Binho base exception class.

    An except block which catches this error will also catch any of the other
    errors defined in this file.
    """


class DeviceNotFoundError(BinhoException, IOError):
    """ Error indicating no Binho host adapter device was found. """


class DeviceBusyError(BinhoException, IOError):
    """ Error indicating the Binho host adapter is too busy to service the given request. """


class DeviceMemoryError(BinhoException, MemoryError):
    """ Error indicating that the Binho host adapter has run out of memory. """


class NotFoundError(BinhoException, IOError):
    """ Error indicating that a resource was not found. """


class BinhoError(BinhoException, RuntimeError):
    """ Runtime error used when no better description is available. """


class ExternalDeviceError(BinhoException, IOError):
    """
    Error used when a external device (e.g. not on the Binho host adapter)
    experiences an issue. This typically means that the error is not wit
    the Binho host adapter hardware or software, but may be with e.g. connections.
    """


class CapabilityError(BinhoException, ValueError):
    """
    Error used when a resource is requested that is out of range.

    For example, requesting an action on pin 6 when there are only 5 pins.
    Or, requesting a DAC be set to 2000 counts when it only goes up to 1024.
    """


class DriverCapabilityError(CapabilityError, NotImplementedError):
    """
    Error used when a resource is requested that this package cannot support.

    This is more specifically for exceptions caused by a limitation of this
    Python package, not the Binho device itself.
    """


class DeviceError(BinhoException, RuntimeError):
    """
    Error used when the device is unable to perform a requested action.

    This could be due to the Binho device being in the wrong state, an external
    device not performing as expected, wires being unplugged, communication
    errors, etc.
    """


BINHO_ERRORS = {
    -2: ValueError,
    -5: NotFoundError,
    -6: DeviceBusyError,
    -7: DeviceMemoryError,
}


def from_binho_error(error_number):
    """
    Returns the error class appropriate for the given Binho host adapter error.
    """
    error_class = BINHO_ERRORS.get(error_number, BinhoError)
    message = "Error {}".format(error_number)
    return error_class(message)
