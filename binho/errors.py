class DeviceNotFoundError(IOError):
    """ Error indicating no Binho host adapter device was found. """


class DeviceInBootloaderError(IOError):
    """ Error indicating a Binho host adapter device was found but it's in bootloader mode. """


class DeviceBusyError(IOError):
    """ Error indicating the Binho host adapter is too busy to service the given request. """


class DeviceMemoryError(MemoryError):
    """ Error indicating that the Binho host adapter has run out of memory. """


class NotFoundError(IOError):
    """ Error indicating that a resource was not found. """


class binhoError(RuntimeError):
    """ Runtime error used when no better description is available. """


class ExternalDeviceError(IOError):
    """
    Error used when a external device (e.g. not on the Binho host adapter)
    experiences an issue. This typically means that the error is not wit
    the Binho host adapter hardware or software, but may be with e.g. connections.
    """


BINHO_ERRORS = {
    -2: ValueError,
    -5: NotFoundError,
    -6: DeviceBusyError,
    -7: MemoryError,
}


def from_binho_error(error_number):
    """
    Returns the error class appropriate for the given Binho host adapter error.
    """
    error_class = BINHO_ERRORS.get(error_number, binhoError)
    message = "Error {}".format(error_number)
    return error_class(message)
