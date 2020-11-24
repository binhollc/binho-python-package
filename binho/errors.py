class binhoError(RuntimeError):
    """ Base binho exception class. """

    pass


class DeviceNotFoundError(binhoError):
    """ Error indicating no Binho host adapter device was found. """

    pass


class DeviceInBootloaderError(binhoError):
    """ Error indicating a Binho host adapter device was found but it's in bootloader mode. """

    pass


class DeviceBusyError(binhoError):
    """ Error indicating the Binho host adapter is too busy to service the given request. """

    pass


class DeviceMemoryError(binhoError):
    """ Error indicating that the Binho host adapter has run out of memory. """

    pass


class NotFoundError(binhoError):
    """ Error indicating that a resource was not found. """

    pass


class ExternalDeviceError(binhoError):
    """
    Error used when a external device (e.g. not on the Binho host adapter)
    experiences an issue. This typically means that the error is not wit
    the Binho host adapter hardware or software, but may be with e.g. connections.
    """

    pass


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
