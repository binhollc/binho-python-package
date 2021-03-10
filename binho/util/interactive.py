"""
Utilities for running Binho host adapter code interactively in IPython.
"""
from IPython.core.error import StdinNotImplementedError

from IPython.core.magic import (
    Magics,
    magics_class,
    line_magic,
)


@magics_class
class binhoShellMagics(Magics):
    """ Class that provides convenience magics for running binho Host Adapter shells. """

    def binho(self):
        return self.shell.user_ns["binho"]

    @line_magic
    def reconnect(self, line):  # pylint: disable=unused-argument
        """ Reconnects to the active binhoHostAdapter, when possible. """

        # Try to reconnect to the attached binhoHostAdapter.
        self.binho().try_reconnect()

    @line_magic
    def reload(self, line):  # pylint: disable=unused-argument
        """ Attempts to reload any modules that have changed. Wrapper for %autoreload. """

        try:
            self.shell.run_magic("autoreload", silent=True)
        except Exception:  # pylint: disable=broad-except
            pass

    @line_magic
    def dmesg(self, line):  # pylint: disable=unused-argument
        """ Print's the binhoHostAdapter's debug buffer. """
        self.binho().dmesg()

    @line_magic
    def resetHW(self, line):  # pylint: disable=unused-argument
        """ Resets the attached binhoHostAdapter, and then reconnects. Hey, %reset was taken. """

        self.binho().reset(reconnect=True)

    @line_magic
    def reset(self, line):
        """Resets the namespace by removing all names defined by the user, if
        called without arguments, or by removing some types of objects, such
        as everything currently in IPython's In[] and Out[] containers (see
        the parameters for details).
        Parameters
        ----------
        -f : force reset without asking for confirmation.
        -r : reset the attached binhoHostAdapter board, as well
        -s : 'Soft' reset: Only clears your namespace, leaving history intact.
            References to objects may be kept. By default (without this option),
            we do a 'hard' reset, giving you a new session and removing all
            references to objects from the current session.
        in - reset input history
        out - reset output history
        dhist - reset directory history
        array - reset only variables that are NumPy arrays
        """

        #
        #  We duplicate the existing %reset code here. Hey, it's BSD.
        #  This code contains stuff that's Copyright (c) 2012 The IPython Development Team.
        #

        # Confirm, as we would for the parent reset.
        opts, args = self.parse_options(line, "sfr", mode="list")

        if "f" in opts:
            ans = True
        else:
            try:
                ans = self.shell.ask_yes_no(
                    "Once deleted, variables cannot be recovered. Proceed (y/[n])?", default="n",
                )
            except StdinNotImplementedError:
                ans = True
        if not ans:
            print("Nothing done.")
            return

        if "r" in opts:
            reset_adapter = True
        else:
            try:
                reset_adapter = self.shell.ask_yes_no(
                    "Would you like to reset the Binho host adapter hardware, as well (y/[n])?", default="n",
                )
            except StdinNotImplementedError:
                reset_adapter = False

        # If we need to reset the Binho host adapter, do so.
        if reset_adapter:
            print("Resetting host adapter.")
            self.binho().reset()

        # Call our inner reset...
        if "s" in opts:  # Soft reset
            user_ns = self.shell.user_ns
            # pylint: disable=no-member
            for i in self.who_ls():
                # pylint: enable=no-member
                del user_ns[i]
        elif len(args) == 0:  # Hard reset
            self.shell.reset(new_session=False)

        # ... and then reconnect to the Binho host adapter.
        binho = self.shell.connect_function()  # pylint: disable=unused-variable
        self.shell.push("binho")
