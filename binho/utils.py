"""
    Utilities that help in writing simple scripts for Binho host adapters.
"""

from __future__ import print_function

from decimal import Decimal

import sys
import ast
import time
import errno
import argparse
import linecache
import os
import urllib.request
import json
import shutil
import psutil
import requests



from . import _binhoHostAdapterSingletonWrapper
from . import binhoHostAdapter
from .errors import DeviceNotFoundError


from .comms.manager import binhoDeviceManager


SI_PREFIXES = {
    "E-12": "p",
    "E-9": "n",
    "E-6": "u",
    "E-3": "m",
    "E+3": "k",
    "E+6": "M",
    "E+9": "G",
    "E+12": "T",
}

# pylint: disable=unused-argument
def log_silent(string, end=None):
    """Silently discards all log data, but provides our logging interface."""
    # pylint: enable=unused-argument


def log_verbose(string, end="\n"):
    """Prints all logging data to the screen."""

    print(string, end=end)
    sys.stdout.flush()


def log_error(string, end="\n"):
    """ Prints errors to stderr. """

    sys.stdout.flush()
    print(string, end=end, file=sys.stderr)
    sys.stderr.flush()


def eng_notation(number, unit=None, separator=" "):
    """ Converts a given number to a nicely-formatted engineering number; so 10e6 would become 10 M."""

    # Grab the raw engineering notation from python's decimal class...
    string = Decimal(number).normalize().to_eng_string()

    # ... and replace the normalized engineering suffix with the relevant SI prefix.
    for normalized, prefix in SI_PREFIXES.items():
        string = string.replace(normalized, separator + prefix)

    if unit is not None:
        string += unit

    return string


def from_eng_notation(string, unit=None, units=None, to_type=None):
    """Converts a string accepted on the command line (potentially in engineering notation) into a
    python number."""

    # Ensure we have a new list of units accessible to us.
    if units is None:
        units = []
    else:
        units = units[:]

    # If we have a single unit specified, absorb it into our units list.
    if unit is not None:
        units.append(unit)

    # If we have an acceptable unit, strip it off before we process things.
    for unitstr in units:
        string = string.replace(unitstr, "")
        string = string.replace(unitstr.upper(), "")
        string = string.replace(unitstr.lower(), "")

    # Strip off any unnecessary whitespace.
    string = string.strip()

    # Replace each SI prefix with its normalized value.
    for normalized, prefix in SI_PREFIXES.items():
        if string.endswith(prefix):
            string = string.replace(prefix, "").strip()
            string += normalized
            break

    # Finally, try to parse the string as a python literal.
    result = ast.literal_eval(string)

    # If we have a post-processing function, apply it.
    if callable(to_type):
        result = to_type(result)

    return result


def human_readable_size(byte_count, unit="B", binary_marker="i"):
    """ Converts a number of bytes into a human-readable size string. """

    SUFFIXES = {
        0: "",
        1: "k" + binary_marker,
        2: "M" + binary_marker,
        3: "G" + binary_marker,
        4: "T" + binary_marker,
        5: "P" + binary_marker,
    }

    if byte_count is None:
        return 0

    suffix_order = 0

    while byte_count >= 1024:
        suffix_order += 1
        byte_count /= 1024

    return "{} {}{}".format(byte_count, SUFFIXES[suffix_order], unit)


class register:
    def __init__(self, initialValue=0x00, widthInBits=8, name="Unnamed Register"):

        self.name = name
        self.widthInBits = widthInBits
        self.value = initialValue

    def getBit(self, bitNumber):
        bitVal = (self.value & (1 << bitNumber)) >> bitNumber
        return bitVal

    def getBits(self, staringfromBit, upToIncludingBit):

        bitMask = 0

        for _ in range((upToIncludingBit - staringfromBit) + 1):
            bitMask = (bitMask << 1) + 1

        bitMask = bitMask << staringfromBit

        bitsVal = (self.value & bitMask) >> staringfromBit

        return bitsVal


class binhoDFUManager:

    cachedManifestData = []
    cachedManifestUrl = ''

    removableDrivesSnapshot = []

    @classmethod
    def switchToNormal(cls, device):

        fwUpdateURL = device.FIRMWARE_UPDATE_URL

        # pylint: disable=unused-variable
        version = binhoDFUManager.getLatestFirmwareVersion(fwUpdateURL)
        url = binhoDFUManager.getLatestFirmwareUrl(fwUpdateURL)
        name = binhoDFUManager.getLatestFirmwareFilename(fwUpdateURL)
        binhoDFUManager.downloadFirmwareFile(url)
        # pylint: enable=unused-variable

        figFileName = binhoDFUManager.getLatestFirmwareFilename(fwUpdateURL)

        binhoDFUManager.takeDrivesSnapshot()

        device.reset_to_bootloader()
        time.sleep(5)

        newDrives = binhoDFUManager.getNewDrives()

        binhoDFUManager.loadFirmwareFile(figFileName, newDrives[0])

        return True



    @classmethod
    def switchToDAPLink(cls, device):

        daplinkUpdateURL = device.DAPLINK_UPDATE_URL

        # pylint: disable=unused-variable
        version = binhoDFUManager.getLatestFirmwareVersion(daplinkUpdateURL)
        url = binhoDFUManager.getLatestFirmwareUrl(daplinkUpdateURL)
        name = binhoDFUManager.getLatestFirmwareFilename(daplinkUpdateURL)
        binhoDFUManager.downloadFirmwareFile(url)
        # pylint: enable=unused-variable

        figFileName = binhoDFUManager.getLatestFirmwareFilename(daplinkUpdateURL)

        binhoDFUManager.takeDrivesSnapshot()

        device.reset_to_bootloader()
        time.sleep(5)

        newDrives = binhoDFUManager.getNewDrives()

        binhoDFUManager.loadFirmwareFile(figFileName, newDrives[0])

        return True

    @classmethod
    def takeDrivesSnapshot(cls):

        snapshot = psutil.disk_partitions()

        binhoDFUManager.removableDrivesSnapshot = [x for x in snapshot if x.opts == 'rw,removable']

    @classmethod
    def getNewDrives(cls):

        snapshot = psutil.disk_partitions()

        rmDrives = [x for x in snapshot if x.opts == 'rw,removable']

        for drive in rmDrives:
            binhoDFUManager.getBootloaderInfo(drive)

        return rmDrives

    @staticmethod
    def getBootloaderInfo(drive):

        btldr_info = drive.mountpoint + '\\INFO.TXT'
        # btldr_details = ''
        productModel = ''
        # boardID = ''

        if os.path.isfile(btldr_info):
            with open(btldr_info, 'r') as file:
                # btldr_details = file.readline().strip()
                productModel = file.readline().strip()
                # boardID = file.readline().strip()

                if productModel.startswith('Model: '):
                    productModel = productModel[7:]


    @staticmethod
    def parseVersionString(verStr):

        ver = verStr.split(".")

        return int(ver[0]), int(ver[1]), int(ver[2])

    @classmethod
    def getJsonManifestParameter(cls, manifestURL, paramName, fail_silent=False):

        try:

            if binhoDFUManager.cachedManifestUrl == manifestURL:
                return binhoDFUManager.cachedManifestData[paramName]

            with urllib.request.urlopen(manifestURL) as url:
                binhoDFUManager.cachedManifestData = json.loads(url.read().decode())
                binhoDFUManager.cachedManifestUrl = manifestURL
                return binhoDFUManager.cachedManifestData[paramName]
        except BaseException:
            if fail_silent:
                return None

            raise RuntimeError(
                "Unable to connect to Binho server and retrieve the data!"
            ) from BaseException

    @classmethod
    def getLatestFirmwareVersion(cls, manifestURL, fail_silent=False):

        return binhoDFUManager.getJsonManifestParameter(manifestURL, 'version', fail_silent)

    @classmethod
    def getLatestFirmwareFilename(cls, manifestURL, fail_silent=False):

        url = binhoDFUManager.getJsonManifestParameter(manifestURL, 'url', fail_silent)

        return url.split('/')[-1]

    @classmethod
    def getLatestFirmwareUrl(cls, manifestURL, fail_silent=False):

        return binhoDFUManager.getJsonManifestParameter(manifestURL, 'url', fail_silent)

    @classmethod
    def downloadFirmwareFile(cls, url, fail_silent=False):

        assetsDir = binho_assets_directory()

        firmwareFilename = url.split('/')[-1]

        try:
            r = requests.get(url)

            with open(assetsDir+"/" + firmwareFilename, "wb") as f:
                f.write(r.content)

            return True
        except BaseException:

            if fail_silent:
                return False
            raise RuntimeError("Failed to download firmware file online!") from BaseException

    # pylint: disable=unused-argument
    @classmethod
    def loadFirmwareFile(cls, figFileName, btldr_drive, fail_silent=False):

        assetsDir = binho_assets_directory()

        firmwareFilename = assetsDir + "/" + figFileName

        if os.path.isfile(firmwareFilename):
            shutil.copy2(firmwareFilename, btldr_drive.mountpoint + '\\fw.uf2')
        else:
            return False

        return True
    # pylint: enable=unused-argument


class binhoArgumentParser(argparse.ArgumentParser):
    """ Convenience-extended argument parser for Binho host adapter. """

    # Serial number expected from a device in DFU.
    DFU_STUB_SERIAL = "dfu_flash_stub"

    def __init__(self, *args, **kwargs):
        """Sets up a Binho-specialized argument parser.
        Additional keyword arguments:
            dfu -- If set to True, DFU-reglated arguments will be provided.
            raise_device_find_failures -- If set to True, this will throw a DeviceNotFoundError
                instead of quitting if no device is present.
        """

        # Determine if we should provide DFU arguments.
        if "dfu" in kwargs:
            self.supports_dfu = kwargs["dfu"]
            del kwargs["dfu"]
        else:
            self.supports_dfu = False

        # Determine if we should provide DFU arguments.
        if "verbose_by_default" in kwargs:
            verbose_by_default = kwargs["verbose_by_default"]
            del kwargs["verbose_by_default"]
        else:
            verbose_by_default = False

        # If set, this will throw DeviceNotFound errors instead of killing the
        # process.
        if "raise_device_find_failures" in kwargs:
            self.raise_device_find_failures = kwargs["raise_device_find_failures"]
            del kwargs["raise_device_find_failures"]
        else:
            self.raise_device_find_failures = False

        # Invoke the core function.
        super().__init__(*args, **kwargs)

        # Start off with no memoized arguments.
        self.memoized_args = None

        # By default, log queietly.

        # Add the standard arguments used to find a Binho host adapter.
        self.add_argument(
            "-d",
            "--device",
            dest="deviceID",
            metavar="<deviceID>",
            type=str,
            help="Serial number of device to look for",
            default=None,
        )
        self.add_argument(
            "-p",
            "--port",
            dest="port",
            metavar="<commport>",
            type=str,
            help="COM port of device to look for",
            default=None,
        )
        self.add_argument(
            "-i",
            "--index",
            dest="index",
            metavar="<i>",
            type=int,
            help="number of the attached device (default: 0)",
            default=0,
        )
        self.add_argument(
            "--wait",
            dest="wait",
            action="store_true",
            help="Wait for a Binho host adapter to come online if none is found.",
        )

        if verbose_by_default:
            self.add_argument(
                "-q",
                "--quiet",
                dest="verbose",
                action="store_false",
                help="Don't log details to the console unless an error occurs.",
            )
        else:
            self.add_argument(
                "-v",
                "--verbose",
                dest="verbose",
                action="store_true",
                help="Log more details to the console.",
            )

        # TODO: specify protocol?
        # TODO: accept comms URI

        # If we're accepting devices from DFU mode, accept the relevant arguments, as well.
        # Note that you must put the device into DFU mode and load the stub
        # from the caller.
        if self.supports_dfu:
            self.add_argument(
                "-d",
                "--dfu",
                dest="dfu",
                action="store_true",
                help="Access a device from in DFU mode by first loading a stub. Always resets.",
            )
            self.add_argument(
                "--dfu-stub",
                dest="dfu_stub",
                metavar="<stub.dfu>",
                type=str,
                help="The stub to use for DFU programming. If not provided, the utility will attempt to automtaically "\
                      + "find one.",
            )

    def find_specified_device(self):
        """ Connects to the Binho host adapter specified by the user's command line arguments. """

        device = None
        args = self.parse_args()

        # Loop until we have a device.
        # Conditions where we should abort are presented below.
        while device is None:
            try:
                device = self._find_binhoHostAdapter(args)

            except DeviceNotFoundError:

                # If we're not in wait mode (or waiting for a DFU flash stub to
                # come up), bail out.
                if not (args.wait or (self.supports_dfu and args.dfu)):

                    # If we're not handling location failures, re-raise the
                    # exception.
                    if self.raise_device_find_failures:
                        raise

                    # Otherwise, print a message and bail out.
                    if args.deviceID:
                        print(
                            "No Binho host adapter found matching Device ID '{}'.".format(
                                args.deviceID
                            ),
                            file=sys.stderr,
                        )
                    elif args.index:
                        print(
                            "No Binho host adapter found with index '{}'.".format(
                                args.index
                            ),
                            file=sys.stderr,
                        )
                    else:
                        print("No Binho host adapter found!", file=sys.stderr)
                    sys.exit(errno.ENODEV)
                else:
                    time.sleep(1)

        return device

    def get_singleton_for_specified_device(self):
        """
        Connects to the Binho host adapter specified by the user's command line arguments, but gets a singleton that
        persists across reconnects.
        """

        # Grab the device itself, and find its deviceID.
        device = self.find_specified_device()
        deviceID = device.serial_number()
        device.close()

        # Create an equivalent singleton wrapper.
        return _binhoHostAdapterSingletonWrapper(deviceID)

    def get_log_function(self):
        """ Returns a function that can be used for logging, but which respects verbosity. """
        return log_verbose if self.parse_args().verbose else log_silent

    def get_log_functions(self):
        """ Returns a 2-tuple of a function that can be used for logging data and errors, attempting to
            repsect -v/-q."""
        return self.get_log_function(), log_error

    # pylint: disable=arguments-differ
    def parse_args(self):
        """ Specialized version of parse_args that memoizes, for Binho host adapters. """

        # If we haven't called parse_args yet, let the base class handle the parsing,
        # first.
        if self.memoized_args is None:
            self.memoized_args = super().parse_args()

        # Always return our memoized version.
        return self.memoized_args
    # pylint: enable=arguments-differ

    @classmethod
    def _find_binhoHostAdapter(cls, args):
        """ Finds a Binho Host Adapter matching the relevant arguments."""

        # If we have an index argument, grab _all_ Binho Host Adapters and
        # select by index ( starts at 1).
        manager = binhoDeviceManager()
        if args.deviceID:

            port = manager.getPortByDeviceID((args.deviceID))

            if port:
                return binhoHostAdapter(deviceID=args.deviceID)
            raise DeviceNotFoundError

        if args.port:
            ports = manager.listAvailablePorts()

            if args.port not in ports:
                raise DeviceNotFoundError
            return binhoHostAdapter(port=args.port)

        if args.index:
            # Find _all_ Binho host adapters
            ports = manager.listAvailablePorts()

            # ... and then select the one with the provided index.
            if len(ports) <= args.index:
                raise DeviceNotFoundError
            return binhoHostAdapter(port=ports[args.index])

        # If we have a serial number, look only for a single device. Theoretically,
        # we should never have more than one Binho host adapter with the same
        # serial number.
        ports = manager.listAvailablePorts()

        # ... and then select the one with the provided index.
        if len(ports) < 1:
            raise DeviceNotFoundError
        return binhoHostAdapter(port=ports[0])


def binho_assets_directory():
    """ Provide a quick function that helps us get at our assets directory. """

    # Find the path to the module, and then find its assets folder.
    module_path = os.path.dirname(__file__)
    return os.path.join(module_path, "assets")


def find_binho_asset(filename):
    """ Returns the path to a given Binho asset, if it exists, or None if the Binho asset isn't provided."""

    asset_path = os.path.join(binho_assets_directory(), filename)

    if os.path.isfile(asset_path):
        return asset_path

    return None


def binho_error_hander():
    # pylint: disable=unused-variable
    exc_type, exc_obj, tb = sys.exc_info()
    # pylint: enable=unused-variable
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)

    print()
    print("Exception in {}, on line {}:".format(filename, lineno))
    print('"{}"'.format(line.strip()))
    print("{}".format(exc_obj))
