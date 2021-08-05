from typing import Any

from binho.errors import DeviceError


class BinhoIODriver:
    def __init__(self, usb, io_number):

        self.usb = usb
        self.io_number = io_number

    @property
    def mode(self) -> str:
        command = f"IO{self.io_number} MODE ?"
        self.usb.sendCommand(command)
        result = self.usb.readResponse()

        if not result.startswith("-IO" + str(self.io_number) + " MODE"):
            raise DeviceError(
                f'Binho responded to command {command} with {result}, not the expected "-IO'
                + str(self.io_number)
                + ' MODE".'
            )

        return result[10:]

    @mode.setter
    def mode(self, mode: str) -> None:
        command = f"IO{self.io_number} MODE {mode}"
        self.usb.sendCommand(command)
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Binho responded to command "{command}" with {result}, not the expected "-OK".')

    @property
    def pwm_frequency(self) -> int:
        command = f"IO{self.io_number} PWMFREQ ?"
        self.usb.sendCommand(command)
        result = self.usb.readResponse()

        if not result.startswith("-IO" + str(self.io_number) + " PWMFREQ"):
            raise DeviceError(
                f'Binho responded to command {command} with {result}, not the expected "-IO'
                + str(self.io_number)
                + ' PWMFREQ".'
            )

        return int(result[13:])

    @pwm_frequency.setter
    def pwm_frequency(self, freq: int) -> None:
        command = f"IO{self.io_number} PWMFREQ {freq}"
        self.usb.sendCommand(command)
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Binho responded to command "{command}" with {result}, not the expected "-OK".')

    @property
    def interrupt_source(self) -> str:
        command = f"IO{self.io_number} INT ?"
        self.usb.sendCommand(command)
        result = self.usb.readResponse()

        if not result.startswith("-IO" + str(self.io_number) + " INT"):
            raise DeviceError(
                f'Binho responded to command {command} with {result}, not the expected "-IO'
                + str(self.io_number)
                + ' INT".'
            )

        return result[8:]

    @interrupt_source.setter
    def interrupt_source(self, int_mode: str) -> None:
        command = f"IO{self.io_number} INT {int_mode}"
        self.usb.sendCommand(command)
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Binho responded to command "{command}" with {result}, not the expected "-OK".')

    @property
    def value(self) -> int:
        command = f"IO{self.io_number} VALUE ?"
        self.usb.sendCommand(command)
        result = self.usb.readResponse()

        if not result.startswith("-IO" + str(self.io_number) + " VALUE"):
            raise DeviceError(
                f'Binho responded to command {command} with {result}, not the expected "-IO'
                + str(self.io_number)
                + ' VALUE".'
            )

        if "%" in result or "V" in result:
            vals = result.split(" ")
            return int(vals[2])

        return int(result[11:])

    @value.setter
    def value(self, value: Any) -> None:
        command = f"IO{self.io_number} VALUE {value}"
        self.usb.sendCommand(command)
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Binho responded to command "{command}" with {result}, not the expected "-OK".')

    def toggle(self, duration):
        command = f"IO{self.io_number} TOGGLE {duration}"
        self.usb.sendCommand(command)
        result = self.usb.readResponse()

        if not result.startswith("-OK"):
            raise DeviceError(f'Binho responded to command "{command}" with {result}, not the expected "-OK".')


    @property
    def interrupt_flag(self) -> bool:
        result = self.usb.interruptCheck("!I0" + str(self.io_number))

        return result

    def clear_interrupt(self) -> None:
        self.usb.interruptClear("!IO" + str(self.io_number))
