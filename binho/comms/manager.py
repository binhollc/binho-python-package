# import usb
# import time
# import struct

# from ..api import CommsBackend
# from ..errors import DeviceNotFoundError


import threading
import queue
import signal
import sys
import serial
import os
import enum
from serial.tools.list_ports import comports


class CommsError(IOError):
    """ Generic class for communications errors. """


class CommandFailureError(CommsError):
    """ Generic class for command failures."""


class binhoDeviceManager:
    def _checkForDeviceID(self, serialPort):
        comport = serial.Serial(
            serialPort, baudrate=1000000, timeout=0.025, write_timeout=0.05
        )
        command = "+ID ?\n"
        comport.write(command.encode("utf-8"))
        receivedData = comport.readline().strip().decode("utf-8")
        if len(receivedData) > 0:
            if receivedData[0] != "-":
                receivedData = comport.readline().strip().decode("utf-8")
        comport.close()
        return receivedData

    def listAvailablePorts(self):

        HWID = "04D8"  # vid:pid
        ports = []

        for port in comports():
            if HWID in port.hwid:
                ports.append(port.device)
        return ports

    def getPortByDeviceID(self, deviceID):
        """
        Get the port address that a specific binho is attached to
        :param deviceID: Device ID string
        :type deviceID: str
        :return: List of ports with a matching device ID
        :rtype: List[str]
        """
        ports = self.listAvailablePorts()
        result = []
        for port in ports:
            try:
                resp = self._checkForDeviceID(port)
                if resp == "-ID " + deviceID:
                    result.append(port)
                elif resp == "-ID 0x" + deviceID:
                    result.append(port)
            except (OSError, serial.SerialException):
                pass

        if len(result) > 0:
            return result[0]
        else:
            return None

    def getUSBVIDPIDByPort(self, comport):

        for port in comports():
            if comport in port.device:
                return port.hwid
        return None
