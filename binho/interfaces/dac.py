from ..errors import CapabilityError
from ..interface import binhoInterface


class DAC(binhoInterface):
    """
    Class representing a Binho host adapter DAC
    """

    PIN_MAPPINGS = {}

    def __init__(self, device, max_voltage=3.3, significant_bits=10, dac_num=0):

        super().__init__(device)

        # Sanity check:
        if dac_num not in (0, 1):
            raise CapabilityError("Specified an unavailable DAC! (Valid values are 0 and 1).")

        self.device = device
        self.api = self.device.apis.io

        self.dac_number = dac_num
        self.maxCounts = 2 ** significant_bits
        self.maxVoltage = max_voltage

    @classmethod
    def registerDAC(cls, name, pin_list):
        cls.PIN_MAPPINGS[name] = pin_list

    def setOutputVoltage(self, value, ioPin=None):

        if ioPin:
            if ioPin in self.PIN_MAPPINGS:
                pin = self.PIN_MAPPINGS[ioPin]
            else:
                raise CapabilityError("Pin {} is not connected to DAC!".format(ioPin))
        else:
            if len(self.PIN_MAPPINGS) > 0:
                pin = next(iter(self.PIN_MAPPINGS.values()))
            else:
                raise CapabilityError("No pins are registered to the DAC!")

        if value > self.maxVoltage or value < 0:
            raise CapabilityError(
                "Voltage of {}V is out of range! DAC range is from 0.0V to {}V".format(value, self.maxVoltage)
            )

        self.api[pin].mode = "AOUT"
        self.api[pin].value = str(value) + "V"

    def setOutputRaw(self, value, ioPin=None):

        if ioPin:
            if ioPin in self.PIN_MAPPINGS:
                pin = self.PIN_MAPPINGS[ioPin]
            else:
                raise CapabilityError("Pin {} is not connected to DAC!".format(ioPin))
        else:
            if len(self.PIN_MAPPINGS) > 0:
                pin = next(iter(self.PIN_MAPPINGS.values()))
            else:
                raise CapabilityError("No pins are registered to the DAC!")

        if value > self.maxCounts or value < 0:
            raise CapabilityError(
                "DAC raw value of {} is out of range! DAC range is from 0 to {}".format(value, self.maxCounts)
            )

        self.api[pin].mode = "AOUT"
        self.api[pin].value = value

    def getDefaultDACPin(self):

        if len(self.PIN_MAPPINGS) > 0:
            return next(iter(self.PIN_MAPPINGS))

        raise CapabilityError("No pins are registered to the DAC!")
