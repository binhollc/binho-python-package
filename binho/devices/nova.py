from typing import Dict

from ..device import binhoDevice
from ..interfaces.gpio import GPIO, GPIOPin
from ..interfaces.dac import DAC
from ..interfaces.adc import ADC

from ..interfaces.i2cBus import I2CBus
from ..interfaces.spiBus import SPIBus
from ..interfaces.oneWireBus import OneWireBus

# from ..programmers.firmware import DeviceFirmwareManager
# from ..interfaces.pattern_generator import PatternGenerator
# from ..interfaces.sdir import SDIRTransceiver


class binhoNova(binhoDevice):
    """ Class representing Binho Nova Multi-Protocol USB Host Adapters. """

    gpio: GPIO
    adc: ADC
    dac: DAC

    gpio_pins: Dict[str, GPIOPin]

    # HANDLED_BOARD_IDS = [2]
    USB_VID_PID = "04D8:ED34"
    PRODUCT_NAME = "Binho Nova"
    FIRMWARE_UPDATE_URL = "https://cdn.binho.io/fw/nova/"

    # The Binho Nova has one LED.
    SUPPORTED_LEDS = 1

    # All of the GPIO mappings accessible from the Binho Nova wire harness.
    # TODO:
    GPIO_MAPPINGS = {
        "IO0": 0,
        "IO1": 1,
        "IO2": 2,
        "IO3": 3,
        "IO4": 4,
    }

    # All of the DAC mappings accessible from the Binho Nova wire harness.
    DAC_MAPPINGS = {
        "IO1": 1,
    }

    # All of the ADC mappings accessible from the Binho Nova wire harness.
    ADC_MAPPINGS = {
        "IO0": 0,
        "IO1": 1,
        "IO2": 2,
        "IO3": 3,
        "IO4": 4,
    }

    @property
    def operationMode(self):
        return self.apis.core.operationMode

    @operationMode.setter
    def operationMode(self, mode):

        if mode == "SPI":

            self.gpio.markPinAsUnused("IO0")
            self.gpio.markPinAsUnused("IO1")
            self.gpio.markPinAsUsed("IO2", True)
            self.gpio.markPinAsUsed("IO3", True)
            self.gpio.markPinAsUsed("IO4", True)

        elif mode == "I2C":

            self.gpio.markPinAsUsed("IO0", True)
            self.gpio.markPinAsUnused("IO1")
            self.gpio.markPinAsUsed("IO2", True)
            self.gpio.markPinAsUnused("IO3")
            self.gpio.markPinAsUnused("IO4")

        elif mode == "UART":

            self.gpio.markPinAsUnused("IO0")
            self.gpio.markPinAsUnused("IO1")
            self.gpio.markPinAsUnused("IO2")
            self.gpio.markPinAsUsed("IO3", True)
            self.gpio.markPinAsUsed("IO4", True)

        else:

            self.gpio.markPinAsUnused("IO0")
            self.gpio.markPinAsUnused("IO1")
            self.gpio.markPinAsUnused("IO2")
            self.gpio.markPinAsUnused("IO3")
            self.gpio.markPinAsUnused("IO4")

        self.apis.core.operationMode = mode

    def initialize_apis(self):
        """ Initialize a new Binho Nova connection. """

        # Set up the core connection.
        super().initialize_apis()

        # Set product name
        self.setProductName(self.PRODUCT_NAME)

        # If the device is in bootloader or DAPLink mode, we don't want to continue
        if self.inBootloaderMode or self.inDAPLinkMode:
            return

        self.gpio = GPIO(self)
        self.adc = ADC(self)
        self.dac = DAC(self)

        # Create our simple peripherals.
        self._populate_simple_interfaces()

        # Initialize the fixed peripherals that come on the board.
        # Populate the per-board GPIO.
        self._populate_gpio(self.gpio, self.GPIO_MAPPINGS)
        self.operationMode = "IO"
        self.gpio_pins = dict()
        for name, line in self.GPIO_MAPPINGS.items():
            pin = GPIOPin(self.gpio, name, line)
            setattr(self, name, pin)
            self.gpio_pins[name] = pin

        self._populate_dac(self.dac, self.DAC_MAPPINGS)

        self._populate_adc(self.adc, self.ADC_MAPPINGS)

        # if self.supports_api('i2c'):
        # print('supports_api i2c success')
        self._add_interface("i2c_busses", [I2CBus(self, "I2C0")])
        self._add_interface("i2c", self.i2c_busses[0])  # pylint: disable=no-member

        # if self.supports_api('spi') and self.supports_api('gpio'):
        #    chip_select = self.gpio.get_pin('J1_P37')
        self._add_interface("spi_busses", [SPIBus(self, 0, "SPI0")])
        self._add_interface("spi", self.spi_busses[0])  # pylint: disable=no-member

        self._add_interface("oneWire_busses", [OneWireBus(self, "1WIRE0")])
        self._add_interface("oneWire", self.oneWire_busses[0])  # pylint: disable=no-member

        # if self.supports_api('uart'):
        # self._add_interface('uart', UART(self))

        # Add objects for each of our LEDs.
        self._populate_leds(self.SUPPORTED_LEDS)

        self.operationMode = "IO"
