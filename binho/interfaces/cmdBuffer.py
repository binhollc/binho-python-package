from ..interface import binhoInterface


class CommandBuffer(binhoInterface):
    """
    Class representing a Binho host adapter Command Buffer.
    """

    # Short name for this type of interface.
    INTERFACE_SHORT_NAME = "cmdbuf"

    def __init__(self, board):
        """
        Initialize the command buffer.

        Args:
            board   -- The Binho host adapter whose Command Buffer we want to control.

        """
        super().__init__(board)

        # Store a reference to the parent board.
        self.api = board.apis.cmdbuf
        self.board = board

    def clear(self):
        """
        Clears the buffer, loop, and trigger settings
        """
        return self.api.clear()

    def add_command(self, command_str):
        """
        Appends the provided command to the tail of the command buffer
        """
        return self.api.add(command_str)

    def loop(self, n_times):
        """
        Instruct command buffer to be looped n_times once triggered
        """
        return self.api.loop(n_times)

    def trigger(self, trigger_event):
        """
        Trigger can be configured for RISE | FALL | CHANGE | NONE on IO1 pin
        """
        return self.api.trigger(trigger_event)

    def force_trigger(self):
        """
        Causes the command buffer to execute immediately.
        """
        return self.api.begin()

