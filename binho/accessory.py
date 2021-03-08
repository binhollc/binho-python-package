#
from binho.errors import DriverCapabilityError


class binhoAccessory:
    """ Base class for objects representing accessory boards. """

    # Optional: subclasses can set this variable to override their accessory name.
    # If not provided, their name will automatically be taken from their class names.
    # This typically doesn't need to be overridden.
    ACCESSORY_NAME = None

    @classmethod
    def get_name(cls):
        """ Default implementation of a function that returns a class's name. """

        # If we have an overridden accessory name, return it.
        if cls.ACCESSORY_NAME:
            return cls.ACCESSORY_NAME

        # Otherwise, return the given class's name.
        return cls.__name__

    @classmethod
    def available_accessories(cls):
        """ Returns a list of available neighbors. """
        return [accessory.get_name() for accessory in cls.__subclasses__()]

    @classmethod
    def from_name(cls, name, board, *args, **kwargs):
        """ Creates a new binhoAccessory object from its name. """

        target_name = name.lower()

        for subclass in cls.__subclasses__():

            # Grab the class's name, and check to see if it matches ours.
            subclass_name = subclass.get_name()

            # If this class matches our target name, this is the class we're looking for!
            # Create an instance and return it.
            if target_name == subclass_name.lower():
                return subclass(board, *args, **kwargs)

        raise DriverCapabilityError("No known driver for accessory '{}'.".format(name))
