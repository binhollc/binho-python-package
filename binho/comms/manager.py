from __future__ import absolute_import

import serial
from serial.tools.list_ports import comports


class binhoDeviceManager:
    @classmethod
    def _checkForDeviceID(cls, serialPort):
        comport = serial.Serial(serialPort, baudrate=1000000, timeout=0.025, write_timeout=0.05)
        command = "+ID ?\n"
        comport.write(command.encode("utf-8"))
        receivedData = comport.readline().strip().decode("utf-8")
        if len(receivedData) > 0:
            if receivedData[0] != "-":
                receivedData = comport.readline().strip().decode("utf-8")
        comport.close()
        return receivedData

    @classmethod
    def listAvailablePorts(cls):

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

        return None

    @classmethod
    def getUSBVIDPIDByPort(cls, comport):

        for port in comports():
            if comport in port.device:
                return port.hwid
        return None
