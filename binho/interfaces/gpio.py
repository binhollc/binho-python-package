from ..interface import binhoInterface

# TODOs:
#  - XXX: Overhaul the GPIO(Collection) class to be more efficient
#  - More cleanup to use the GPIOPin model.
#  - Support ranges of pins from the same port (GPIOPort objects?)
#  - Implement a release function so if e.g. an I2C device is no longer in use
#    it releases its pins back to the GPIO pool.


class ioPinModes:
    digitalInput = "DIN"
    digitalOutput = "DOUT"
    analogInput = "AIN"
    analogOutput = "AOUT"
    pwmOutput = "PWM"


class GPIOProvider(binhoInterface):
    """ Base class for an object that provides access to GPIO pins. """

    # If the subclass has a fixed set of pins, it can override this mapping to
    # specify the fixed pin names to be automatically registered.
    FIXED_GPIO_PINS = {}

    # If the subclass doesn't want to allow external sources to register GPIO
    # pins
    ALLOW_EXTERNAL_REGISTRATION = True

    def __init__(self, board, name_mappings=None):
        """Sets up the basic fields for a GPIOProvider.
        Parameters:
            name_mappings -- Allows callers to rename the local / fixed GPIO pin names.
                Optional; accepts a dictionary mapping their fixed names to their new names, or
                to None to remove the relevant pin from the list of available pins.
                This allows instantiators to give a given GPIO collection more specific names, or
                to hide them from general API display/usage.
        """

        super().__init__(board)

        if name_mappings is None:
            name_mappings = {}

        # Set up our basic tracking parameters, which track which GPIO pins
        # are available and in use.
        self.pin_mappings = {}
        self.active_gpio = {}
        self.available_pins = []

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
            self.__registerGPIO(board, name, line)

    def registerGPIO(self, board, name, line, used=False):
        """
        Registers a GPIO pin for later use. Usually only used in board setup.
        Args:
            name -- The name for the GPIO, usually expressed as IO#.
            line -- An abstract argument passed to subclass methods that serves
                to identify the pin. Subclasses often use this to store e.g. port and pin
                numbers.
        """

        # If this class doesn't allow pin registration, raise an error.
        if not self.ALLOW_EXTERNAL_REGISTRATION:
            raise NotImplementedError("This GPIO collection does not allow registration of new pins.")

        # Otherwise, delegate to our internal registration method.
        self.__registerGPIO(board, name, line, used)

    def __registerGPIO(self, board, name, line, used=False):
        """
        Registers a GPIO pin for later use. Usually only used in board setup.
        Args:
            name -- The name for the GPIO, usually expressed as IO[n].
            line -- An abstract argument passed to subclass methods that serves
                to identify the pin. Subclasses often use this to store e.g. port and pin
                numbers.
        """

        # Store the full name in our pin mappings.
        self.pin_mappings[name] = line
        board.addIOPinAPI(name, line)

        if not used:
            self.markPinAsUnused(name)

    def markPinAsUsed(self, name):
        """ Marks a pin as used by another peripheral. """

        if name not in self.pin_mappings:
            raise ValueError("Unknown GPIO pin {}".format(name))

        self.available_pins.remove(name)

    def markPinAsUnused(self, name):
        """ Mark a pin as no longer used by another peripheral. """

        if name not in self.pin_mappings:
            raise ValueError("Unknown GPIO pin {}".format(name))

        if name not in self.available_pins:
            self.available_pins.append(name)

    def getAvailablePins(self, include_active=True):  # pylint: disable=unused-argument
        """ Returns a list of available GPIO names. """
        available = self.available_pins[:]
        available.extend(self.active_gpio.keys())

        return sorted(available)

    def getPin(self, name, unique=False):
        """
        Returns a GPIOPin object by which a given pin can be controlled.
        Args:
            name -- The GPIO name to be used.
            unique -- True if this should fail if a GPIO object for this pin
                already exists.
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
        raise ValueError("No available GPIO pin {}".format(name))

    def releasePin(self, gpio_pin):
        """
        Releases a GPIO pin back to the system for re-use, potentially
        not as a GPIO.
        """

        if gpio_pin.name not in self.active_gpio:
            raise ValueError("Trying to release a pin we don't own!")

        # Mark the pin as an input, placing it into High-Z mode.
        # TODO: Disable any pull-ups present on the pin.
        gpio_pin.mode = ioPinModes.digitalInput

        # Remove the GPIO pin from our active array, and add it back to the
        # available pool.
        del self.active_gpio[gpio_pin.name]
        self.markPinAsUnused(gpio_pin.name)

    def setPinMode(self, line, mode, initial_value=False):
        """
        Configure a GPIO line for use as an input or output.  This must be
        called before the line can be used by other functions.
        Parameters:
            line      -- A unique identifier for the given pin that has meaning to the subclass.
            direction -- Directions.IN (input) or Directions.OUT (output)
        """

    def setPinValue(self, line, state):
        """
        Set the state of an output line.  The line must have previously been
        configured as an output using setup().
        Parameters:
            line  -- A unique identifier for the given pin that has meaning to the subclass.
            state -- True sets line high, False sets line low
        """

    def readPinValue(self, line):
        """
        Get the state of an input line.  The line must have previously been
        configured as an input using setup().
        Args:
            line  -- A unique identifier for the given pin that has meaning to the subclass.
        Return:
            bool -- True if line is high, False if line is low
        """

    def getPinMode(self, line):
        """
        Gets the direction of a GPIO pin.
        Args:
            line  -- A unique identifier for the given pin that has meaning to the subclass.
        Return:
            bool -- True if line is an output, False if line is an input
        """

    def getPinIndex(self, line):
        """Returns the 'pin number' for a given GPIO pin.
        This number is typically the 'bit number' in a larger, organized port. For providers
        in which this isn't a valid semantic concept, any convenient semantic identifier (or None)
        is acceptable.
        """

    def getPinIdentifier(self, line):
        """Returns the 'pin number' for a given GPIO pin.
        This number is typically the 'bit number' in a larger, organized port. For providers
        in which this isn't a valid semantic concept, any convenient semantic identifier (or None)
        is acceptable.
        """


class GPIO(GPIOProvider):
    """ Work with the GPIO directly present on the Binho host adapter. """

    def __init__(self, board):
        """
        Args:
            board -- Binho host adapter whose GPIO lines are to be controlled
        """

        # store information about the our low-level connection.
        self.board = board

        # Set up our basic fields...
        super().__init__(self.board)

    def setPinMode(self, line, mode, initial_value=False):
        """
        Configure a GPIO line for use as an input or output.  This must be
        called before the line can be used by other functions.
        Args:
            line -- (port, pin); typically a tuple from J1, J2, J7 below
            direction -- Directions.IN (input) or Directions.OUT (output)
        TODO: allow pull-up/pull-down resistors to be configured for inputs
        """
        self.board.apis.io[line].mode = mode

        if mode == "DOUT" and initial_value:
            self.board.apis.io[line].value = 1

    def setPinValue(self, line, state):
        """
        Set the state of an output line.  The line must have previously been
        configured as an output using setup().
        Args:
            line -- (port, pin); typically a tuple from J1, J2, J7 below
            state -- True sets line high, False sets line low
        """

        # TODO: validate GPIO direction?

        self.board.apis.io[line].value = state

    def readPinValue(self, line):
        """
        Get the state of an input line.  The line must have previously been
        configured as an input using setup().
        Args:
            line -- (port, pin); typically a tuple from J1, J2, J7 below
        Return:
            bool -- True if line is high, False if line is low
        """

        return self.board.apis.io[line].value

    def getPWMFrequency(self, line):

        return self.board.apis.io[line].pwmFrequency

    def setPWMFrequency(self, line, freq):

        self.board.apis.io[line].pwmFrequency = freq

    def getPinMode(self, line):
        """
        Gets the direction of a GPIO pin.
        Args:
            line -- (port, pin); typically a tuple from J1, J2, J7 below
        Return:
            bool -- True if line is an output, False if line is an input
        """

        return self.board.apis.io[line].mode

    def getPinIndex(self, line):
        """ Returns the 'port number' for a given GPIO pin."""
        return line

    def getPinIdentifier(self, line):
        """ Returns the 'pin number' for a given GPIO pin. """
        return "IO" + str(line)


class GPIOPin:
    """
    Class representing a single GPIO pin.
    """

    def __init__(self, gpio_provider, name, line):
        """
        Creates a new object representing a GPIO Pin. Usually instantiated via
        a GPIO object.
        Args:
            gpio_provider -- The GPIO object to which this pin belongs.
            name -- The name of the given pin. Should match a name registered
                in its GPIO collection.
            line -- The pin's 'line' information, as defined by the object that created
                this GPIO pin. This variable has semantic meaning to the GPIO collection;
                but doesn't have any semantic meaning to this class.
        """

        self.name = name
        self._parent = gpio_provider
        self._line = line

        # Set up the pin for use. Idempotent.
        self._parent.setPinMode(self._line, "DIN")

    @property
    def mode(self):
        return self._parent.getPinMode(self._line)

    @mode.setter
    def mode(self, ioPinMode, initial_value=False):
        """
        Sets the GPIO pin to use a given mode.
        """
        modeStr = "DIN"

        if ioPinMode == ioPinModes.digitalInput:
            modeStr = "DIN"
        elif ioPinMode == ioPinModes.digitalOutput:
            modeStr = "DOUT"
        elif ioPinMode == ioPinModes.analogInput:
            modeStr = "AIN"
        elif ioPinMode == ioPinModes.analogOutput:
            modeStr = "AOUT"
        elif ioPinMode == ioPinModes.pwmOutput:
            modeStr = "PWM"

        self._parent.setPinMode(self._line, modeStr, initial_value)

    @property
    def value(self):
        """ Returns the value of a GPIO pin. """
        raw = self._parent.readPinValue(self._line)
        return raw

    @value.setter
    def value(self, value):
        self._parent.setPinValue(self._line, value)

    @property
    def pwmFreq(self):
        return self._parent.getPWMFrequency(self._line)

    @pwmFreq.setter
    def pwmFreq(self, freq):
        self._parent.setPWMFrequency(self._line, freq)

    @property
    def pinNumber(self):
        """ Returns pin's pin number within its port, if possible. """
        return self._parent.getPinIndex(self._line)

    @property
    def pinName(self):
        """ Returns pin's full pin name """
        return self._parent.getPinIdentifier(self._line)
