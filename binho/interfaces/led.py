from ..interface import binhoInterface


class LED(binhoInterface):
    """ Simple periheral that allows control of an LED through the binhoHostAdapter HAL."""

    def __init__(self, device, led_number):
        """Create a new object representing a binho host adapter LED.
        device -- The Binho Host Adapter device object that owns the given LED.
        led_number -- The one-indexed LED number.
        """
        super().__init__(device)

        # Store a reference to the parent device.
        self.device = device

        # Store a reference to the api
        self.api = device.apis.core

        # Store which of the four(?) LEDs we refer to.
        self.led_number = led_number

    # Function that turns off the relevant LED value. """
    def off(self):
        return self.api.setLEDRGB(0, 0, 0)

    def setRGB(self, red, green, blue):
        return self.api.setLEDRGB(red, green, blue)

    def setColor(self, color):
        return self.api.setLEDColor(color)
