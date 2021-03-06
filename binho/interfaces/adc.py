from ..errors import CapabilityError
from ..interface import binhoInterface


class ADC(binhoInterface):
    """
    Class representing a Binho host adapter ADC, which defaults to ADC 0 connected to J2_P5 on Azaela, with 10
    significant bits."""

    PIN_MAPPINGS = {}

    def __init__(self, device, max_voltage=3.3, significant_bits=12, adc_num=0):

        super().__init__(device)

        # Sanity check:
        if adc_num not in (0, 1):
            raise CapabilityError("Specified an unavailable ADC! (Valid values are 0 and 1).")

        self.device = device
        self.api = self.device.apis.io

        # Get ADC pin number for device pin
        self.adc_number = adc_num
        self.maxCounts = 2 ** significant_bits
        self.maxVoltage = max_voltage

    @classmethod
    def registerADC(cls, name, pin_list):
        cls.PIN_MAPPINGS[name] = pin_list

    def readInputVoltage(self, ioPin=None):

        if ioPin:
            if ioPin in self.PIN_MAPPINGS:
                pin = self.PIN_MAPPINGS[ioPin]
            else:
                raise CapabilityError("Pin {} is not connected to ADC!".format(ioPin))
        else:
            if len(self.PIN_MAPPINGS) > 0:
                pin = next(iter(self.PIN_MAPPINGS.values()))
            else:
                raise CapabilityError("No pins are registered to the ADC!")

        self.api[pin].mode = "AIN"
        voltage = float("%.3f" % (self.api[pin].value / self.maxCounts * self.maxVoltage))

        return voltage

    def readInputRaw(self, ioPin=None):

        if ioPin:
            if ioPin in self.PIN_MAPPINGS:
                pin = self.PIN_MAPPINGS[ioPin]
            else:
                raise CapabilityError("Pin {} is not connected to ADC!".format(ioPin))
        else:
            if len(self.PIN_MAPPINGS) > 0:
                pin = next(iter(self.PIN_MAPPINGS.values()))
            else:
                raise CapabilityError("No pins are registered to the ADC!")

        self.api[pin].mode = "AIN"

        return self.api[pin].value

    def getDefaultADCPin(self):

        if len(self.PIN_MAPPINGS) > 0:
            return next(iter(self.PIN_MAPPINGS))

        raise CapabilityError("No pins are registered to the ADC!")
