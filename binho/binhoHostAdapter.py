from .device import binhoDevice
from .devices import nova  # pylint: disable=unused-import

# Ensure that we have access to all Binho host adapter devices. Normally, we'd avoid
# importing an entire namespace, but in this case, this allows us to ensure
# that all board modules are loaded for autoidentification.
from .errors import DeviceNotFoundError

active_connections = {}


def binhoHostAdapter(**board_identifiers):
    """
    Attempts to create a new instance of binhoHostAdapter board (sub)class
    most applicable to the given device. For example, if the attached
    board is a Binho Nova, this will automatically create a
    binhoNova object.
    Accepts the same arguments as pyusb's usb.find() method, allowing narrowing
    to a more specific binhoHostAdapter by e.g. serial number. Like usb.find(), providing
    find_all will return a list of all found devices.
    Throws a DeviceNotFoundError if no device is avaiable and find_all is not set.
    """
    if not board_identifiers:
        board_identifiers["index"] = 0
        return binhoDevice.autodetect(board_identifiers)

    if (
        "port" in board_identifiers
        and board_identifiers["port"]
        or "deviceID" in board_identifiers
        and board_identifiers["deviceID"]
        or "index" in board_identifiers
    ):
        return binhoDevice.autodetect(board_identifiers)

    if "find_all" in board_identifiers and board_identifiers["find_all"]:
        return binhoDevice.autodetect_all(board_identifiers)

    raise DeviceNotFoundError


def binhoHostAdapterSingleton(serial=None):
    """ Returns a binhoHostAdapter object, re-using an existing object if we already have a connection to the given
        binhoHostAdapter. """

    # If we already have a binhoHostAdapter with the given serial,
    if serial in active_connections:
        device = active_connections[serial]
        if device.comms.still_connected():
            return device

    # Otherwise, try to create a new binhoHostAdapter instance.
    hostAdapter = binhoHostAdapter(serial_number=serial)
    active_connections[serial] = hostAdapter

    return hostAdapter
