from typing import Dict

from ..device import binhoDevice
from ..interfaces.gpio import GPIOPin

# from ..interfaces.dac import DAC
# from ..interfaces.adc import ADC

from ..interfaces.i2cBus import I2CBus
from ..interfaces.spiBus import SPIBus
from ..interfaces.oneWireBus import OneWireBus

# from ..programmers.spiFlash import SPIFlash
# from ..programmers.firmware import DeviceFirmwareManager
# from ..interfaces.pattern_generator import PatternGenerator
# from ..interfaces.sdir import SDIRTransceiver
# from ..interfaces.uart import UART


class binhoProtonovaSPI(binhoDevice):
    """ Class representing Binho Nova Multi-Protocol USB Host Adapters. """

    gpio_pins: Dict[str, GPIOPin]

    # HANDLED_BOARD_IDS = [2]
    USB_VID_PID = "04D8:EAEA"
    PRODUCT_NAME = "Binho Protonova SPI"

    SUPPORTED_LEDS = 1

    # All of the GPIO mappings accessible from the Binho Protonova Package.
    # TODO:
    GPIO_MAPPINGS = {
        "IO0": 0,
        "IO1": 1,
        "IO2": 2,
        "IO3": 3,
        "IO4": 4,
    }

    # All of the ADC mappings accessible from the Binho Protonova Package.
    ADC_MAPPINGS = {
        "IO0": [(0, 0), (1, 0)],
        "IO1": [(0, 0), None],
        "IO2": [None, (1, 6)],
        "IO3": [(0, 5), (1, 5)],
        "IO4": [(0, 2), (1, 2)],
    }

    # name, scu port and pin, scu function number
    UART_MAPPINGS = [
        {
            "J1_P33": ((9, 5), 7),  # TX
            "J1_P34": ((9, 6), 7),  # RX
            "J1_P35": ((2, 0), 1),  # TX
            "J2_P35": ((2, 1), 1),  # RX
            "J7_P2": ((6, 4), 2),  # TX
            "J7_P3": ((6, 5), 2),  # RX
        },
        {
            "J1_P25": ((1, 14), 1),  # RX
            "J1_P26": ((1, 13), 1),  # TX
            "J1_P27": ((5, 6), 4),  # TX
            "J2_P28": ((3, 4), 4),  # TX
            "J2_P37": ((3, 5), 4),  # RX
        },
        {
            "J1_P28": ((1, 15), 1),  # TX
            "J1_P30": ((1, 16), 1),  # RX
            "J2_P23": ((7, 2), 6),  # RX
            "J2_P25": ((7, 1), 6),  # TX
        },
        {"J2_P8": ((4, 2), 6), "J2_P19": ((2, 4), 2), "J2_P20": ((2, 3), 2),},  # RX  # RX  # TX
    ]

    def initialize_apis(self):
        """ Initialize a new Binho Protonova connection. """

        # Set up the core connection.
        super().initialize_apis()

        # TODO: Implement these?
        # gpio = GPIO(self)
        # adc = ADC(self)
        # dac = DAC(self)

        # Set product name
        self.setProductName(self.PRODUCT_NAME)

        # Create our simple peripherals.
        self._populate_simple_interfaces()

        # Initialize the fixed peripherals that come on the board.
        # Populate the per-board GPIO.
        # if self.supports_api("gpio"):
        # self._populate_gpio(gpio, self.GPIO_MAPPINGS)
        # self.gpio_pins = dict()
        # for name, line in self.GPIO_MAPPINGS.items():
        #     pin = GPIOPin(gpio, name, line)
        #     setattr(self, name, pin)
        #     self.gpio_pins[name] = pin

        # if self.supports_api("adc"):
        # self._populate_adc(self.adc, self.ADC_MAPPINGS)

        # if self.supports_api('i2c'):
        # print('supports_api i2c success')
        self._add_interface("i2c_busses", [I2CBus(self, "I2C0")])
        self._add_interface("i2c", [I2CBus(self, "I2C0")])

        # if self.supports_api('spi') and self.supports_api('gpio'):
        #    chip_select = self.gpio.get_pin('J1_P37')
        self._add_interface("spi_busses", [SPIBus(self, 0, "SPI0")])
        self._add_interface("spi", [SPIBus(self, 0, "SPI0")])

        self._add_interface("oneWire_busses", [OneWireBus(self, "1WIRE0")])
        self._add_interface("oneWire", [OneWireBus(self, "1WIRE0")])

        # if self.supports_api('uart'):
        # self._add_interface('uart', UART(self))

        # if self.supports_api("jtag"):
        #    try:
        #        self._add_interface('jtag', JTAGChain(self))
        #    except:
        #        pass

        # if self.supports_api('sdir'):
        #    self._add_interface('sdir', SDIRTransceiver(self))

        # Add objects for each of our LEDs.
        self._populate_leds(self.SUPPORTED_LEDS)
