#!/usr/bin/env python3
#
# Console I/O handling; lifted from pyserial/miniterm.py, which uses the same BSD license.
#       (C)2002-2017 Chris Liechti <cliechti@gmx.net>
#

import os
import sys
import codecs
import msvcrt
import ctypes
import termios
import fcntl
import atexit

# Python 2/3 compatible method for using raw_input, and unicode-aware chr.
from binho.errors import DriverCapabilityError

try:
    raw_input
except NameError:
    raw_input = input
    unichr = chr


class ConsoleBase:
    """OS abstraction for console (input/output codec, no echo)"""

    def __init__(self):
        if sys.version_info >= (3, 0):
            self.byte_output = sys.stdout.buffer
        else:
            self.byte_output = sys.stdout
        self.output = sys.stdout

    def setup(self):
        """Set console to read single characters, no echo"""

    def cleanup(self):
        """Restore default console settings"""

    @classmethod
    def getkey(cls):
        """Read a single key from the console"""
        return None

    def write_bytes(self, byte_string):
        """Write bytes (already encoded)"""

        if isinstance(byte_string, tuple):
            byte_string = byte_string[0]

        self.byte_output.write(byte_string)
        self.byte_output.flush()

    def write(self, text):
        """Write string"""
        self.output.write(text)
        self.output.flush()

    def cancel(self):
        """Cancel getkey operation"""

    #  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -
    # context manager:
    # switch terminal temporary to normal mode (e.g. to get user input)

    def __enter__(self):
        self.cleanup()
        return self

    def __exit__(self, *args, **kwargs):
        self.setup()


class NTConsole(ConsoleBase):
    class Out:
        """file-like wrapper that uses os.write"""

        def __init__(self, fd):
            self.fd = fd

        def flush(self):
            pass

        def write(self, s):
            os.write(self.fd, s)

    def __init__(self):

        super().__init__()
        self._saved_ocp = ctypes.windll.kernel32.GetConsoleOutputCP()
        self._saved_icp = ctypes.windll.kernel32.GetConsoleCP()
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
        self.output = codecs.getwriter("UTF-8")(self.Out(sys.stdout.fileno()), "replace")
        # the change of the code page is not propagated to Python, manually fix
        # it
        sys.stderr = codecs.getwriter("UTF-8")(self.Out(sys.stderr.fileno()), "replace")
        sys.stdout = self.output
        self.output.encoding = "UTF-8"  # needed for input

    def __del__(self):

        ctypes.windll.kernel32.SetConsoleOutputCP(self._saved_ocp)
        ctypes.windll.kernel32.SetConsoleCP(self._saved_icp)

    def getkey(self):

        while True:
            z = msvcrt.getwch()
            if z == unichr(13):
                return unichr(10)
            if z in (unichr(0), unichr(0x0E)):  # functions keys, ignore
                msvcrt.getwch()
            else:
                return z

    def cancel(self):

        # CancelIo, CancelSynchronousIo do not seem to work when using
        # getwch, so instead, send a key to the window with the console
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        ctypes.windll.user32.PostMessageA(hwnd, 0x100, 0x0D, 0)


class POSIXConsole(ConsoleBase):
    def __init__(self):

        super().__init__()
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        atexit.register(self.cleanup)

    def setup(self):

        new = termios.tcgetattr(self.fd)
        new[3] = new[3] & ~termios.ICANON & ~termios.ECHO & ~termios.ISIG
        new[6][termios.VMIN] = 1
        new[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, new)

    def getkey(self):
        try:
            c = sys.stdin.buffer.read(1)
        except AttributeError:
            c = sys.stdin.read(1)

        if c == unichr(0x7F):
            c = unichr(8)  # map the BS key (which yields DEL) to backspace
        return c

    def cancel(self):
        fcntl.ioctl(self.fd, termios.TIOCSTI, b"\0")

    def cleanup(self):

        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old)


def Console():
    """ Factory method that returns the Console object most appropriate for the current OS envrionment. """

    if os.name == "posix":
        return POSIXConsole()
    if os.name == "nt":
        return NTConsole()

    raise DriverCapabilityError("Console support not implemented for OS '{}'.".format(os.name))
