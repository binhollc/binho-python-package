from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Any, Optional, Mapping, Dict, List, Union, Set

from ..comms.device import binhoAPI
from ..errors import CapabilityError, DriverCapabilityError, DeviceError
from ..interface import binhoInterface

# TODOs:
#  - XXX: Overhaul the GPIO(Collection) class to be more efficient
#  - More cleanup to use the GPIOPin model.
#  - Support ranges of pins from the same port (GPIOPort objects?)
#  - Implement a release function so if e.g. an I2C device is no longer in use
#    it releases its pins back to the GPIO pool.


class IOMode(Enum):
    """
    All valid modes for a GPIO pin.

    :cvar DIN: Digital input.
    :cvar DOUT: Digital output.
    :cvar AIN: Analog input.
    :cvar AOUT: Analog output.
    :cvar PWM: Pulse-width modulated output.
    """

    DIN = "DIN"
    DOUT = "DOUT"
    AIN = "AIN"
    AOUT = "AOUT"
    PWM = "PWM"


class GPIOProvider(binhoInterface, metaclass=ABCMeta):
    """
    Base class for an object that provides access to GPIO pins.

    :cvar FIXED_GPIO_PINS: If a subclass has a fixed set of pins, it can
        override this mapping to specify the fixed pin names to be automatically
        registered.
    :type FIXED_GPIO_PINS: Mapping[str, str]
    :cvar ALLOW_EXTERNAL_REGISTRATION: A subclass may set this to False to
        disallow external sources to register GPIO pins.
    :type ALLOW_EXTERNAL_REGISTRATION: bool
    """

    FIXED_GPIO_PINS: Mapping[str, str] = {}
    ALLOW_EXTERNAL_REGISTRATION: bool = True

    pin_mappings: Dict[str, Any]
    active_gpio: Dict[str, "GPIOPin"]
    available_pins: Set[str]

    def __init__(self, board: binhoAPI, name_mappings: Optional[Mapping[str, str]] = None) -> None:
        """
        Sets up the basic fields for a GPIOProvider.

        :param board: The Binho device to control GPIO on.
        :type board: binhoAPI
        :param name_mappings: Allows callers to rename the local / fixed GPIO
            pin names. Optional; accepts a dictionary mapping their fixed names
            to their new names, or to None to remove the relevant pin from the
            list of available pins. This allows instantiators to give a given
            GPIO collection more specific names, or to hide them from general
            API display/usage.
        :type name_mappings: Optional[Mapping[str, str]]
        """

        super().__init__(board)

        if name_mappings is None:
            name_mappings = {}

        # Set up our basic tracking parameters, which track which GPIO pins
        # are available and in use.
        self.pin_mappings = {}
        self.active_gpio = {}
        self.available_pins = set()
        self._hw_used_pins: Set[str] = set()

        # Add all of our fixed pins as acceptable GPIO.
        for name, line in self.FIXED_GPIO_PINS.items():

            # If we've been asked to rename the given pin, register it under
            # the new name, rather than under the provided name,
            if name in name_mappings:
                name = name_mappings[name]

            # If our name field winds up remapping to 'None', the instantiator
            # is trying to hide the relevant pin. Skip registering it.
            if name is None:
                continue

            # Register each fixed GPIO.
            self._registerGPIO(name, line)

    def registerGPIO(self, name: str, line: Any, used: bool = False) -> None:
        """
        Registers a GPIO pin for later use.

        Usually only used in board setup. Will also mark the pin as unused by
        default. Will raise an exception if ``ALLOW_EXTERNAL_REGISTRATION`` is
        False.

        :param name: The name for the pin, usually expressed as IO#.
        :type name: str
        :param line: An abstract argument passed to subclass methods that serves
            to identify the pin. Subclasses often use this to store e.g. port
            and pin numbers.
        :type line: Any
        :param used: True to NOT mark the pin as unused. Optional, defaults to
            False.
        :type used: bool
        :return: None.
        :rtype: None
        """

        # If this class doesn't allow pin registration, raise an error.
        if not self.ALLOW_EXTERNAL_REGISTRATION:
            raise DriverCapabilityError("This GPIO collection does not allow registration of new pins.")

        # Otherwise, delegate to our internal registration method.
        self._registerGPIO(name, line, used)

    def _registerGPIO(self, name: str, line: Any, used: bool = False) -> None:
        """
        Registers a GPIO pin for later use.

        Usually only used in board setup. Will also mark the pin as unused by
        default.

        Will allow registration even if ``ALLOW_EXTERNAL_REGISTRATION`` is True.

        :param name: The name for the pin, usually expressed as IO#.
        :type name: str
        :param line: An abstract argument passed to subclass methods that serves
            to identify the pin. Subclasses often use this to store e.g. port
            and pin numbers.
        :type line: Any
        :param used: True to NOT mark the pin as unused. Optional, defaults to
            False.
        :type used: bool
        :return: None.
        :rtype: None
        """
        # Store the full name in our pin mappings.
        self.pin_mappings[name] = line
        self.device.addIOPinAPI(name, line)

        if not used:
            self.markPinAsUnused(name)

    def markPinAsUsed(self, name: str, _hw: bool = False) -> None:
        """
        Marks a pin as used by another peripheral.

        :param name: The name of the pin, usually expressed as IO#.
        :type name: str
        :param _hw: Set True to indicate that the hardware is consuming this pin
            (e.g. I2C, SPI). If True, an error will NOT be raised if this pin
            was already marked used by another call where ``_hw`` was True.
            End user code must NOT use this parameter.
        :type _hw: bool
        :return: None.
        :rtype: None
        """
        if name not in self.pin_mappings:
            raise CapabilityError("Unknown GPIO pin {}".format(name))

        try:
            self.available_pins.remove(name)
        except KeyError as e:
            if _hw and name in self._hw_used_pins:
                pass
            else:
                raise CapabilityError(f"GPIO pin {name} is already in use!") from e

        if _hw:
            self._hw_used_pins.add(name)

    def markPinAsUnused(self, name: str) -> None:
        """
        Mark a pin as no longer used by another peripheral.

        :param name: The name of the pin, usually expressed as IO#.
        :type name: str
        :return: None.
        :rtype: None
        """
        if name not in self.pin_mappings:
            raise CapabilityError("Unknown GPIO pin {}".format(name))

        self.available_pins.add(name)
        try:
            self._hw_used_pins.remove(name)
        except KeyError:
            pass

    def getAvailablePins(self, include_active: bool = True) -> List[str]:  # pylint: disable=unused-argument
        """
        Return a list of available GPIO names.

        :param include_active: TODO: Evaluate removal.
        :type include_active: bool
        :return: A list of available GPIO names, in alphabetical order.
        :rtype: List[str]
        """
        available = list(self.available_pins)
        available.extend(self.active_gpio.keys())

        return sorted(available)

    def getPin(self, name: str, unique: bool = False) -> "GPIOPin":
        """
        Return a GPIOPin object by which a given pin can be controlled.

        :param name: The name of the pin, usually expressed as IO#.
        :type name: str
        :param unique: If True, an exception will be raised if the pin is
            already used, even if as a GPIO. Defaults to False.
        :type unique: bool
        :return: A GPIOPin object managing the named pin.
        :rtype: GPIOPin
        """
        if str(name).isnumeric():
            name = "IO" + str(name)

        name = name.upper()

        # If we already have an active GPIO pin for the relevant name, return
        # it.
        if name in self.active_gpio and not unique:
            return self.active_gpio[name]

        # If the pin's available for GPIO use, grab it.
        if name in self.available_pins:
            port = self.pin_mappings[name]

            self.active_gpio[name] = GPIOPin(self, name, port)
            self.markPinAsUsed(name)

            return self.active_gpio[name]

        # If we couldn't create the GPIO pin, fail out.
        raise CapabilityError("No available GPIO pin {}".format(name))

    def releasePin(self, gpio_pin: "GPIOPin") -> None:
        """
        Releases a GPIO pin back to the system for re-use, potentially
        not as a GPIO.
        """

        if gpio_pin.name not in self.active_gpio:
            raise CapabilityError(f"Can't release non-owned GPIO pin {gpio_pin.name}.")

        # Mark the pin as an input, placing it into High-Z mode.
        # TODO: Disable any pull-ups present on the pin.
        gpio_pin.mode = IOMode.DIN

        # Remove the GPIO pin from our active array, and add it back to the
        # available pool.
        del self.active_gpio[gpio_pin.name]
        self.markPinAsUnused(gpio_pin.name)

    @abstractmethod
    def setPinMode(self, line: Any, mode: IOMode, initial_value: bool = False) -> None:
        """
        Configure a GPIO line for use as an input or output.  This must be
        called before the line can be used by other functions.
        Parameters:
            line      -- A unique identifier for the given pin that has meaning to the subclass.
            direction -- Directions.IN (input) or Directions.OUT (output)
        """

    @abstractmethod
    def setPinValue(self, line: Any, value: Any) -> None:
        """
        Set the state of an output line.  The line must have previously been
        configured as an output using setup().
        Parameters:
            line  -- A unique identifier for the given pin that has meaning to the subclass.
            value -- The value to send to the device. Could be an integer or a string voltage or percentage.
        """

    @abstractmethod
    def readPinValue(self, line: Any) -> int:
        """
        Get the state of an input line.  The line must have previously been
        configured as an input using setup().
        Args:
            line  -- A unique identifier for the given pin that has meaning to the subclass.
        Return:
            bool -- The integer value (counts or boolean) reported by the device.
        """

    @abstractmethod
    def getPinMode(self, line: Any) -> IOMode:
        """
        Gets the direction of a GPIO pin.
        Args:
            line  -- A unique identifier for the given pin that has meaning to the subclass.
        Return:
            IOMode
        """

    @abstractmethod
    def getPinIndex(self, line: Any) -> Optional[int]:
        """Returns the 'pin number' for a given GPIO pin.
        This number is typically the 'bit number' in a larger, organized port. For providers
        in which this isn't a valid semantic concept, any convenient semantic identifier (or None)
        is acceptable.
        """

    @abstractmethod
    def getPinIdentifier(self, line: Any) -> str:
        """Returns the 'pin name' for a given GPIO pin."""

    @abstractmethod
    def getPWMFrequency(self, line: Any) -> int:
        """
        Get the PWM frequency, in Hertz, for a given GPIO pin.

        Subclasses may not implement this method if it is not applicable.
        """

    def setPWMFrequency(self, line: Any, freq: int):
        """
        Set the PWM frequency, in Hertz, for a given GPIO pin.

        Subclasses may not implement this method if it is not applicable.
        """

    @abstractmethod
    def toggle(self, line: Any, duration: int):
        """
        Toggle a given GPIO pin for a specified duration of microseconds

        Subclasses may not implement this method if it is not applicable.
        """



class GPIO(GPIOProvider):
    """ Work with the GPIO directly present on the Binho host adapter. """

    def __init__(self, board: binhoAPI):
        """
        Args:
            board -- Binho host adapter whose GPIO lines are to be controlled
        """

        # Set up our basic fields...
        super().__init__(board)

    def setPinMode(self, line: Any, mode: Union[str, IOMode], initial_value: bool = False) -> None:
        """
        Configure a GPIO line for use as an input or output.  This must be
        called before the line can be used by other functions.
        Args:
            line -- (port, pin); typically a tuple from J1, J2, J7 below
            direction -- Directions.IN (input) or Directions.OUT (output)
        TODO: allow pull-up/pull-down resistors to be configured for inputs
        """
        if not isinstance(mode, IOMode):
            mode = IOMode(mode)
        self.device.apis.io[line].mode = mode.value

        if mode == "DOUT" and initial_value:
            self.device.apis.io[line].value = 1

    def setPinValue(self, line: Any, value: int) -> None:
        """
        Set the state of an output line.  The line must have previously been
        configured as an output using setup().
        Args:
            line -- (port, pin); typically a tuple from J1, J2, J7 below
            value -- The value to send to the device. Could be an integer or a string voltage or percentage.
        """
        # TODO: validate GPIO direction?
        try:
            value = int(value)  # helps coerce bools
        except ValueError:
            pass
        self.device.apis.io[line].value = value

    def readPinValue(self, line: Any) -> int:
        """
        Get the state of an input line.  The line must have previously been
        configured as an input using setup().
        Args:
            line -- (port, pin); typically a tuple from J1, J2, J7 below
        Return:
            int -- 0 or 1 for digital, 0-1024 for analog/PWM.
        """
        return self.device.apis.io[line].value

    def getPWMFrequency(self, line: Any) -> int:
        """Get the PWM frequency, in Hertz, for a given GPIO pin."""
        return self.device.apis.io[line].pwm_frequency

    def setPWMFrequency(self, line: Any, freq: int) -> None:
        """Set the PWM frequency, in Hertz, for a given GPIO pin."""
        self.device.apis.io[line].pwm_frequency = freq

    def toggle(self, line: Any, duration: int) -> None:
        """Toggle a given GPIO pin for a specified duration of microseconds."""
        self.device.apis.io[line].toggle(duration)


    def getPinMode(self, line: Any) -> str:
        """
        Gets the direction of a GPIO pin.
        Args:
            line -- (port, pin); typically a tuple from J1, J2, J7 below
        Return:
            bool -- True if line is an output, False if line is an input
        """
        mode = self.device.apis.io[line].mode
        try:
            return IOMode(mode)
        except ValueError:
            raise DeviceError(f"Binho reports IO mode {mode}, which is not a valid IOMode.")  # pylint: disable=raise-missing-from

    def getPinIndex(self, line: Any) -> int:
        """ Returns the 'pin number' for a given GPIO pin."""
        return int(line)

    def getPinIdentifier(self, line: Any) -> str:
        """ Returns the 'pin name' for a given GPIO pin. """
        return "IO" + str(line)


class GPIOPin:
    """
    Class representing a single GPIO pin.

    :ivar name: The name of the managed pin, as defined by the target device.
    :type name: str
    """

    name: str

    def __init__(self, gpio_provider: GPIOProvider, name: str, line: Any) -> None:
        """
        Create a new object managing a single GPIO pin.

        This should always be done at device initialization; end user code
        should not create ``GPIOPin`` instances.

        :param gpio_provider: The GPIO object to which this pin belongs.
        :type gpio_provider: GPIOProvider
        :param name: The name of the given pin. Should match a name registered
            in its GPIO collection.
        :type name: str
        :param line: The pin's 'line' information, as defined by the object that
            created this GPIO pin. This variable has semantic meaning to the
            GPIO collection; but doesn't have any semantic meaning to this
            class.
        :type line: Any
        """

        self.name = name
        self._parent: GPIOProvider = gpio_provider
        self._line: Any = line
        self._used: bool = False

        # Set up the pin for use. Idempotent.
        self._parent.setPinMode(self._line, IOMode.DIN)

    @property
    def mode(self) -> Optional[IOMode]:
        """
        Get the current IO mode of this pin.

        :getter: Get the current IO mode of this pin.
        :setter: Set the IO mode of this pin, unless already in use.
        :return: The current IO mode of this pin, or None if unused.
        :rtype: IOMode
        """
        if self._used:
            return self._parent.getPinMode(self._line)
        return None

    @mode.setter
    def mode(self, mode: Optional[IOMode]) -> None:
        """
        Sets the GPIO pin to use a given mode.

        Not all pins support all modes. Please refer to the documentation for
        your specific device.

        :param mode: The mode to set, or None to mark the pin as unused. Note
            that to change device operation mode to one which requires pins you
            have previously configured an mode for, you must first set the mode
            of those pins to None.
        :type mode: Optional[IOMode] (but will accept string too)
        """
        if mode is None:
            self._parent.markPinAsUnused(self.name)
            self._used = False
        else:
            if not self._used:
                self._parent.markPinAsUsed(self.name)
                self._used = True
            self._parent.setPinMode(self._line, mode, False)

    @property
    def value(self) -> int:
        """
        Get the value of a GPIO pin.

        :getter: Get the value of a GPIO pin.
        :setter: Set the value of a GPIO pin configured as output.
        :return: The value from the device in integer form. For digital IO, this
            is 0 or 1. For analog IO or PWM outputs, this is 0-1024.
        :rtype: int
        """
        return self._parent.readPinValue(self._line)

    @value.setter
    def value(self, value: Any):
        """
        Set the value of a GPIO pin configured as output.

        :param value: The value to set. Could be a boolean True or False or
            integer 1 or 0 for digital outputs; could be an integer count 0 to
            1024 or string voltage (e.g. "2.5V") for analog outputs; could be
            an integer count 0 to 1024 or string percentage (e.g. "50%") for
            PWM outputs.
        :type value: Any
        :return:
        :rtype:
        """
        self._parent.setPinValue(self._line, value)

    @property
    def pwm_freq(self) -> int:
        """
        Get the PWM frequency of this pin.

        Some pins' PWM frequencies are linked. Please refer to the documentation
        for your specific device.

        This property may raise an exception if accessed when this pin is not in
        PWM mode.

        :getter: Get the PWM frequency, if in PWM mode.
        :setter: Set the PWM frequency, if in PWM mode.
        :return: The PWM frequency.
        :rtype: int
        """
        return self._parent.getPWMFrequency(self._line)

    @pwm_freq.setter
    def pwm_freq(self, freq: int) -> None:
        """
        Set the PWM frequency of this pin.

        Some pins' PWM frequencies are linked. Please refer to the documentation
        for your specific device.

        This property may raise an exception if accessed when this pin is not in
        PWM mode.

        :param freq: The PWM frequency.
        :type freq: int
        :return: None.
        :rtype None
        """
        self._parent.setPWMFrequency(self._line, freq)

    def toggle(self, duration: int) -> None:
        """
        Toggle a given GPIO pin for a specified duration of microseconds.
        Minimum duration is ~5microseconds, max duration is 256 milliseconds.

        This property may raise an exception if called when this pin is not in
        DOUT mode.

        :param duration: The duration of the pulse in microseconds.
        :type duration: int
        :return: None.
        :rtype None
        """
        if 0 <= duration <= 256000:
            self._parent.toggle(self._line, duration)
        else:
            raise CapabilityError("Toggle duration range is from 0 to 256000 microseconds!")

    @property
    def pin_number(self) -> Optional[int]:
        """
        Get this pin's number/index within its port, if possible.

        :getter: Get this pin's number within its port, if possible.
        :setter: None, read-only/computed.
        :return: This pin's number within its port.
        :rtype: Optional[int]
        """
        return self._parent.getPinIndex(self._line)

    @property
    def pin_name(self) -> str:
        """
        Get this pin's full name.

        :getter: Get this pin's full name.
        :setter: None, read-only/computed.
        :return: This pin's full name.
        :rtype: str
        """
        return self._parent.getPinIdentifier(self._line)
