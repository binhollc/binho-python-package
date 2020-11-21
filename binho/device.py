"""
Module containing the core definitions for a binhoDevice.
"""

import string
from weakref import WeakSet

from .comms.device import binhoAPI

from .interfaces.led import LED
from .interfaces.gpio import GPIO
from .interfaces.adc import ADC
from .interfaces.dac import DAC

# from .interfaces.uart import UART

# from .interfaces.pattern_generator import PatternGenerator
# from .interfaces.sdir import SDIRTransceiver

from . import programmers as ProgrammerModules
from .programmers.eeprom import EEPROM

from .programmers import *

# from .programmers.m0 import M0Coprocessor
# from .programmers.firmware import DeviceFirmwareManager

# from .glitchkit import *


# from .debug.lpc43xx import LPC43xxTarget

# Default device identifiers.
BINHO_VENDOR_ID = 0x1D50
BINHO_PRODUCT_ID = 0x60E6

# Quirk constant that helps us identify libusb's pipe errors, which bubble
# up as generic USBErrors with errno 32 on affected platforms.
# LIBUSB_PIPE_ERROR = 32

# Total seconds we should wait after a reset before reconnecting.
RECONNECT_DELAY = 3


class binhoDevice(binhoAPI):
    """
    Class describing Binho host adapters.
    """

    # Default device identifiers.
    BOARD_VENDOR_ID = 0x1D50
    BOARD_PRODUCT_ID = 0x60E6

    """
    The mappings from GPIO names to port numbers. Paths in names can be delineated
    with underscores to group gpios. For example, if Jumper 7, Pin 3 is Port 5, Pin 11,
    you could add an entry that reads "J7_P3": (5, 11).
    """
    GPIO_MAPPINGS = {}

    SIMPLE_CLASS_MAPPINGS = {"gpio": ("gpio", GPIO)}

    def __init__(self, *args, **kwargs):
        """ Initialize a new binhoDevice instance with our additional properties. """

        # Create a new list of interfaces and programmers.
        self._interfaces = []
        self._instantiated_programmers = WeakSet()
        super(binhoDevice, self).__init__(*args, **kwargs)

    def available_interfaces(self):
        """ Returns a list of peripheral properties that exist on this board. """
        return self._interfaces[:]

    def _populate_leds(self, led_count):
        """Adds the standard set of LEDs to the board object.
        Args:
            led_count -- The number of LEDS present on the board.
        """

        self._add_interface("leds", {})

        for i in range(1, led_count + 1):
            self.leds[i] = LED(self, i)

    def _populate_gpio(self):
        """ Adds GPIO pin definitions to the board's main GPIO object. """

        # Handle each GPIO mapping.
        for name, pin in self.GPIO_MAPPINGS.items():
            self.gpio.registerGPIO(name, pin)

    def _populate_adc(self):
        """Adds ADC definitions to the board."""

        # Handle each ADC mapping.
        for name, pin in self.ADC_MAPPINGS.items():
            ADC.registerADC(name, pin)

        self.adc = ADC(self)

    def _populate_dac(self):
        """Adds DAC definitions to the board."""

        # Handle each ADC mapping.
        for name, pin in self.DAC_MAPPINGS.items():
            DAC.registerDAC(name, pin)

        self.dac = DAC(self)

    def _add_interface(self, name, instance):
        """
        Adds a peripheral to the Binho host adapter object. Prefer this over adding attributes directly,
        as it adds peripherals to a list that can be queried by the user.
        Arguments:
            name -- The name of the attribute to add to this board. "i2c" would create a
                .i2c property on this board.
            instance -- The object to add as that property.
        """

        self._interfaces.append(name)
        setattr(self, name, instance)

    def _add_simple_interface(self, name, cls, *args, **kwargs):
        """Adds a given interface to this board.
        Arguments:
            name -- The attribute name to be added to the board.
            cls -- The class to be instantiated to create the given object.
        """

        # Create an instance of the relevant peripheral class...
        instance = cls(self, *args, **kwargs)

        # ... and add it to this board.
        self._add_interface(name, instance)

    def _populate_simple_interfaces(self):
        """ Adds simple interfaces to the board object by parsing the SIMPLE_CLASS_MAPPINGS dictionary. """

        for comms_class, interface in self.SIMPLE_CLASS_MAPPINGS.items():

            name, python_class = interface
            self._add_simple_interface(name, python_class)

    def available_accessories(self):
        """ Returns the list of available accessory drivers. """
        return binhoAccessory.available_accessories()

    def attach_accessory(self, name, *args, **kwargs):
        """ Returns the list of available accessory drivers. """

        # Create a new object for the given neighbor...
        accessory = binhoAccessory.from_name(name, self, *args, **kwargs)

        # TODO: register this and add it to a .accessory object?

        return accessory

    def available_programmers(self, as_dictionary=False):
        """ Returns the list of available programmers. """

        from types import ModuleType

        programmers = {}

        for module in ProgrammerModules.__dict__.values():
            if isinstance(module, ModuleType) and hasattr(module, "create_programmer"):
                module_name = module.__name__.split(".")[-1]
                programmers[module_name] = module

        if as_dictionary:
            return programmers
        else:
            return list(programmers.values())

    def create_programmer(self, name, *args, **kwargs):
        """ Creates a new instance of the programmer with the given name. """

        try:
            programmer_module = self.available_programmers(True)[name]
            programmer = programmer_module.create_programmer(self, *args, **kwargs)

            # Keep a weak reference to the relevant programmer.
            # This is useful for re-attaching programmers after a disconnect.
            self._instantiated_programmers.add(programmer)

            # Finally, return the created programmer.
            return programmer

        except KeyError:
            raise KeyError("no available programmer named {}".format(name))

    def __dir__(self):
        """ Generate a cleaned-up dir listing for the relevant board. """

        items = super(binhoDevice, self).__dir__()
        return [item for item in items if item[0] in string.ascii_lowercase]
