"""
    Utilities that help in writing simple scripts for Binho host adapters.
"""

from __future__ import print_function

from decimal import Decimal

import sys
import platform
import ast
import time
import errno
import argparse
import os
import tempfile
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


class binhoDFUManager:

    _fw_releases_url = "releases.json"
    _fw_latest_url = "latest/latest.json"
    _daplink_latest_url = "latest/latest_dap.json"

    cachedManifestData = []
    cachedManifestUrl = ""

    removableDrivesSnapshot = []

    bootloaderInfo = {"version": "unknown", "model": "unknown", "boardID": "unknown"}

    @classmethod
    def switchToBootloader(cls, device):

        binhoDFUManager.takeDrivesSnapshot()

        device.reset_to_bootloader()
        time.sleep(8)

        newDrive = binhoDFUManager.getNewDrives()

        return newDrive

    @classmethod
    def switchToNormal(cls, device, release=None):

        fw_image_url = binhoDFUManager.getFirmwareImageUrl(device.FIRMWARE_UPDATE_URL, release)

        if fw_image_url:

            figFilePath = binhoDFUManager.downloadFirmwareFile(fw_image_url)

            bootloaderDrive = binhoDFUManager.switchToBootloader(device)

            binhoDFUManager.loadFirmwareFile(figFilePath, bootloaderDrive)

            return True

        return False

    @classmethod
    def switchToDAPLink(cls, device):

        fw_image_url = binhoDFUManager.getFirmwareImageUrl(device.FIRMWARE_UPDATE_URL, daplink=True)

        if fw_image_url:
            figFilePath = binhoDFUManager.downloadFirmwareFile(fw_image_url)

            bootloaderDrive = binhoDFUManager.switchToBootloader(device)

            binhoDFUManager.loadFirmwareFile(figFilePath, bootloaderDrive)

            return True

        return False

    @classmethod
    def takeDrivesSnapshot(cls):

        snapshot = psutil.disk_partitions()

        binhoDFUManager.removableDrivesSnapshot = [x for x in snapshot if x.opts == "rw,removable"]

    @classmethod
    def getNewDrives(cls):

        snapshot = psutil.disk_partitions()

        if platform.system() == "Windows":
            rmDrives = [x for x in snapshot if ("rw" in x.opts and "removable" in x.opts)]
        else:
            rmDrives = snapshot

        for drive in rmDrives:
            if binhoDFUManager.getBootloaderInfo(drive):
                return drive

        return None

    @staticmethod
    def getBootloaderInfo(drive):

        # btldr_info = drive.mountpoint + "\\INFO.TXT"
        btldr_info = os.path.join(drive.mountpoint, "INFO.TXT")

        if os.path.isfile(btldr_info):
            with open(btldr_info, "r") as file:
                binhoDFUManager.bootloaderInfo["version"] = file.readline().strip()
                productModel = file.readline().strip()
                boardID = file.readline().strip()

                if productModel.startswith("Model: "):
                    binhoDFUManager.bootloaderInfo["model"] = productModel[7:]

                if boardID.startswith("Board-ID: "):
                    binhoDFUManager.bootloaderInfo["boardID"] = boardID[10:]
                    return True
        return False

    @staticmethod
    def getBootloaderVersion(drive):

        btldr_version = "unknown"

        # btldr_info = drive.mountpoint + "\\INFO.TXT"
        btldr_info = os.path.join(drive.mountpoint, "INFO.TXT")

        if os.path.isfile(btldr_info):
            with open(btldr_info, "r") as file:
                # pylint: disable=unused-variable
                btldr_version = file.readline().strip()
                productModel = file.readline().strip()
                boardID = file.readline().strip()
                # pylint: enable=unused-variable

        return btldr_version

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
        except Exception as e:
            if fail_silent:
                return None

            raise RuntimeError("Unable to connect to Binho server and retrieve the data!") from e

    @classmethod
    def getLatestFirmwareVersion(cls, base_url, fail_silent=False):

        manifestURL = base_url + binhoDFUManager._fw_latest_url

        return binhoDFUManager.getJsonManifestParameter(manifestURL, "version", fail_silent)

    @classmethod
    def getLatestFirmwareFilename(cls, base_url, fail_silent=False):

        manifestURL = base_url + binhoDFUManager._fw_latest_url

        url = binhoDFUManager.getJsonManifestParameter(manifestURL, "url", fail_silent)

        return url.split("/")[-1]

    @classmethod
    def getLatestFirmwareUrl(cls, base_url, fail_silent=False):

        manifestURL = base_url + binhoDFUManager._fw_latest_url

        return binhoDFUManager.getJsonManifestParameter(manifestURL, "url", fail_silent)

    @classmethod
    def getFirmwareImageUrl(cls, base_url, release=None, daplink=False, fail_silent=False):

        if not release:

            manifestURL = base_url + binhoDFUManager._fw_latest_url

            if daplink:
                manifestURL = base_url + binhoDFUManager._daplink_latest_url

            return binhoDFUManager.getJsonManifestParameter(manifestURL, "url", fail_silent)

        manifestURL = base_url + binhoDFUManager._fw_releases_url

        with urllib.request.urlopen(manifestURL) as url:
            data = json.loads(url.read().decode())

            for r in data["releases"]:
                if r["version"] == release:
                    return r["url"]

        return None

    @classmethod
    def getFirmwareFilename(cls, firmware_image_url):

        return firmware_image_url.split("/")[-1]

    @classmethod
    def getAvailableFirmwareReleases(cls, base_url):

        manifestURL = base_url + binhoDFUManager._fw_releases_url
        releases = []

        with urllib.request.urlopen(manifestURL) as url:
            data = json.loads(url.read().decode())

            for r in data["releases"]:
                releases.append(r["version"])

        return releases

    @classmethod
    def isFirmwareVersionAvailable(cls, base_url, release):

        avail_releases = binhoDFUManager.getAvailableFirmwareReleases(base_url)

        if release in avail_releases:
            return True

        return False

    @classmethod
    def downloadFirmwareFile(cls, url, fail_silent=False):

        fd, path = tempfile.mkstemp()

        try:
            r = requests.get(url)

            with os.fdopen(fd, "wb") as tmp:
                # do stuff with temp file
                tmp.write(r.content)

            return path

        except Exception as e:
            if fail_silent:
                return False
            raise RuntimeError("Failed to download firmware file online!") from e

    # pylint: disable=unused-argument
    @classmethod
    def loadFirmwareFile(cls, figFilePath, btldr_drive, fail_silent=False):

        firmwareDestination = os.path.join(btldr_drive.mountpoint, "fw.uf2")

        if os.path.isfile(figFilePath):
            shutil.copy2(figFilePath, firmwareDestination)
        else:
            return False

        # clean up fig file
        os.remove(figFilePath)

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
                "-v", "--verbose", dest="verbose", action="store_true", help="Log more details to the console.",
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
                help="The stub to use for DFU programming. If not provided, the utility will attempt to automtaically "
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
                            "No Binho host adapter found matching Device ID '{}'.".format(args.deviceID),
                            file=sys.stderr,
                        )
                    elif args.index:
                        print(
                            "No Binho host adapter found with index '{}'.".format(args.index), file=sys.stderr,
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
