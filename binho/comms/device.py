# import usb
import os
import collections
from dataclasses import dataclass
from typing import Dict, Any

import hid

from ..errors import DeviceNotFoundError

from .manager import binhoDeviceManager
from .comms import binhoComms
from .drivers.core import binhoCoreDriver
from .drivers.i2c import binhoI2CDriver
from .drivers.spi import binhoSPIDriver
from .drivers.io import BinhoIODriver
from .drivers.onewire import binho1WireDriver


@dataclass
class _BinhoAPIs:
    core: binhoCoreDriver
    i2c: binhoI2CDriver
    spi: binhoSPIDriver
    oneWire: binho1WireDriver
    io: Dict[Any, BinhoIODriver]
    swi: None = None
    uart: None = None


# pylint: disable=too-many-instance-attributes
class binhoAPI:

    HANDLED_BOARD_IDS = []
    USB_VID_PID = "04D8"

    # Default device identifiers.
    BOARD_VENDOR_ID = 0x1D50
    BOARD_PRODUCT_ID = 0x60E6

    apis: _BinhoAPIs

    @classmethod
    def populate_default_identifiers(cls, device_identifiers, find_all=False):
        """
        Populate a dictionary of default identifiers-- which can
        be overridden or extended by arguments to the function.
        device_identifiers -- any user-specified identifers; will override
            the default identifiers in the event of a conflit
        """

        # By default, accept any device with the default vendor/product IDs.
        identifiers = {
            "idVendor": cls.BOARD_VENDOR_ID,
            "idProduct": cls.BOARD_PRODUCT_ID,
            "find_all": find_all,
        }
        identifiers.update(device_identifiers)

        return identifiers

    def __init__(self, **device_identifiers):

        self.name = "Unknown"
        self.serialPort = device_identifiers["port"]
        self.comms = binhoComms(device_identifiers["port"])

        self.apis = _BinhoAPIs(
            core=binhoCoreDriver(self.comms),
            i2c=binhoI2CDriver(self.comms),
            spi=binhoSPIDriver(self.comms),
            oneWire=binho1WireDriver(self.comms),
            io=collections.OrderedDict(),
            swi=None,
            uart=None,
        )

        self.handler = None
        self.manager = None
        self.interrupts = None
        self._stopper = None
        self._txdQueue = None
        self._rxdQueue = None
        self._intQueue = None
        self._debug = os.getenv("BINHO_NOVA_DEBUG")

        self._inBootloader = False
        self._inDAPLinkMode = False

        self._hid_serial_number = "UNKNOWN"
        self._hid_path = None

        # By default, accept any device with the default vendor/product IDs.
        self.identifiers = self.populate_default_identifiers(device_identifiers)

        # For convenience, allow serial_number=None to be equivalent to not
        # providing a serial number: a board with any serial number will be
        # accepted.
        if "serial_number" in self.identifiers and self.identifiers["serial_number"] is None:
            del self.identifiers["serial_number"]

        # TODO: replace this with a comms_string
        # Create our backend connection to the device.
        # self.comms = CommsBackend.from_device_uri(**self.identifiers)

        # Get an object that allows easy access to each of our APIs.
        # self.apis = self.comms.generate_api_object()

        # TODO: optionally use the core API to discover other APIs

        # Final sanity check: if we don't handle this board ID, bail out!
        # if self.HANDLED_BOARD_IDS and (self.board_id() not in self.HANDLED_BOARD_IDS):
        #    raise DeviceNotFoundError()

    # Destructor
    def __del__(self):
        self.comms.close()

    # Public functions
    @classmethod
    def autodetect(cls, board_identifiers):
        # Iterate over each subclass of binhoHostAdapter until we find a board
        # that accepts the given board ID.

        for subclass in cls.__subclasses__():
            if subclass.accepts_connected_device(board_identifiers):

                # Create an instance of the device to return,
                # and ensure that device has fully populated comms APIs.
                board = subclass(**board_identifiers)

                board.initialize_apis()

                return board

        # If we couldn't find a board, raise an error.
        raise DeviceNotFoundError

    @classmethod
    def autodetect_all(cls, device_identifiers):
        """
        Attempts to create a new instance of the Binho host adapter subclass
        most applicable for each board present on the system-- similar to the
        behavior of autodetect.
        Accepts the same arguments as pyusb's usb.find() method, allowing narrowing
        to a more specific Binho Host Adapter by e.g. serial number.
        Returns a list of Binho Host Adapters, which may be empty if none are found.
        """

        devices = []

        # Iterate over each subclass of Binho host adapters until we find a board
        # that accepts the given board ID.
        for subclass in cls.__subclasses__():

            # Get objects for all devices accepted by the given subclass.

            subclass_devices = subclass.all_accepted_devices(**device_identifiers)

            # NOTE: It's possible that two classes may choose to both advertise support
            # for the same device, in which case we'd wind up with duplicats here. We could
            # try to filter out duplicates using e.g. USB bus/device, but that assumes
            # things are USB connected.
            devices.extend(subclass_devices)

        # Ensure each device has its comms objects fully populated.
        for device in devices:
            device.initialize_apis()

        # Return the list of all subclasses.
        return devices

    @classmethod
    # pylint: disable=unused-argument
    def all_accepted_devices(cls, **device_identifiers):
        # pylint: enable=unused-argument
        """
        Returns a list of all devices supported by the given class. This should be
        overridden if the device connects via anything other that USB.
        Accepts the same arguments as pyusb's usb.find() method, allowing narrowing
        to a more specific Binho host adapter by e.g. serial number.
        """

        devices = []

        # Grab the list of all devices that we theoretically could use.
        manager = binhoDeviceManager()
        availablePorts = manager.listAvailablePorts()
        identifiers = {}

        # Iterate over all of the connected devices, and filter out the devices
        # that this class doesn't connect.
        for port in availablePorts:

            # We need to be specific about which device in particular we're
            # grabbing when we query things-- or we'll get the first acceptable
            # device every time. The trick here is to populate enough information
            # into the identifier to uniquely identify the device. The address
            # should do, as pyusb is only touching enmerated devices.
            identifiers["port"] = port
            identifiers["find_all"] = False

            # If we support the relevant device _instance_, and it to our list.
            if cls.accepts_connected_device(identifiers):
                devices.append(cls(**identifiers))

        return devices

    @classmethod
    def accepts_connected_device(cls, device_identifiers):
        """
        Returns true iff the provided class is appropriate for handling a connected
        Binho host adapter.
        Accepts the same arguments as pyusb's usb.find() method, allowing narrowing
        to a more specific Binho host adapter by e.g. serial number.
        """

        manager = binhoDeviceManager()

        if "deviceID" in device_identifiers and device_identifiers["deviceID"]:

            port = manager.getPortByDeviceID(device_identifiers["deviceID"])
            device_identifiers["port"] = port

        elif "index" in device_identifiers:

            ports = manager.listAvailablePorts()
            if len(ports) <= device_identifiers["index"]:
                raise DeviceNotFoundError
            device_identifiers["port"] = ports[device_identifiers["index"]]

        try:

            usb_hwid = manager.getUSBVIDPIDByPort(device_identifiers["port"])

        except DeviceNotFoundError:
            return False

        # Accept only Binho host adapters whose board IDs are handled by this
        # class. This is mostly used by subclasses, which should override
        # HANDLED_BOARD_IDS.
        if usb_hwid:
            return cls.USB_VID_PID in usb_hwid

        return False

    def setProductName(self, productname):
        self.name = productname

    @property
    def deviceID(self):
        """Reads the board ID number for the device."""

        if not self._inBootloader and not self._inDAPLinkMode:
            return self.apis.core.deviceID.upper()

        return self._hid_serial_number.upper()

    @property
    def commPort(self):
        return self.serialPort

    @classmethod
    def usb_info(cls, port):
        usb_info = binhoDeviceManager.getUSBVIDPIDByPort(port)
        return usb_info

    @property
    def productName(self):
        """Returns the human-readable product-name for the device."""
        return self.name

    @property
    def firmwareVersion(self):
        """Reads the board's firmware version."""
        return self.apis.core.firmwareVersion

    @property
    def hardwareVersion(self):
        return self.apis.core.hardwareVersion

    @property
    def commandVersion(self):
        return self.apis.core.commandVersion

    @property
    def inBootloaderMode(self):
        return self._inBootloader

    @property
    def inDAPLinkMode(self):
        return self._inDAPLinkMode

    def initialize_apis(self):
        """Hook-point for sub-boards to initialize their APIs after
        we have comms up and running and auto-enumeration is complete.

        :raises Exception: Will raise some exception if initialization did not
            succeed.
        """

        # Open up the commport.
        self.comms.start()

        try:
            # see if it's in DAPLink mode
            _ = self.deviceID
            self._inDAPLinkMode = False
            self._inBootloader = False

        except Exception:  # pylint: disable=broad-except
            h = hid.device()
            h.open(
                int(self.USB_VID_PID.split(":")[0], 16), int(self.USB_VID_PID.split(":")[1], 16), # pylint: disable=use-maxsplit-arg
            )

            self._hid_serial_number = "0x" + h.get_serial_number_string()

            if h.get_product_string() == "CMSIS-DAP":
                self._inDAPLinkMode = True
                self._inBootloader = False

            else:
                self._inDAPLinkMode = False
                self._inBootloader = True

    def addIOPinAPI(self, name, ioPinNumber):  # pylint: disable=unused-argument
        self.apis.io[ioPinNumber] = BinhoIODriver(self.comms, ioPinNumber)

    def supports_api(self, class_name):
        """ Returns true iff the board supports the given API class. """
        return hasattr(self.apis, class_name)

    @classmethod
    def version_warnings(cls):
        """Returns any warning messages relevant to the device's firmware version.
        Can be used to warn the user when an upgrade is required.
        Returns a string with any warnings, or None  if no warnings apply.
        """
        return None

    def reset_to_bootloader(self):

        if self._inDAPLinkMode:
            h = hid.device()
            h.open(
                int(self.USB_VID_PID.split(":")[0], 16), # pylint: disable=use-maxsplit-arg
                int(self.USB_VID_PID.split(":")[1], 16),
                self._hid_serial_number[2:],
            )
            h.set_nonblocking(1)
            h.write([0x00, 0x80])

        else:
            self.apis.core.resetToBtldr(fail_silent=True)

    def exit_bootloader(self):

        if self._inBootloader:
            h = hid.device()
            h.open(
                int(self.USB_VID_PID.split(":")[0], 16), # pylint: disable=use-maxsplit-arg
                int(self.USB_VID_PID.split(":")[1], 16),
                self._hid_serial_number[2:],
            )
            h.set_nonblocking(1)
            h.write([0x00, 0x48, 0x03, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])

    def close(self):
        self.comms.close()


def _to_hex_string(byte_array):
    """Convert a byte array to a hex string."""

    hex_generator = ("{:02x}".format(x) for x in byte_array)
    return "".join(hex_generator)


# pylint: enable=too-many-instance-attributes
