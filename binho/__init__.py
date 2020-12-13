# Alias objects to make them easier to import.

from .binhoHostAdapter import binhoHostAdapter
from .binhoHostAdapter import binhoHostAdapterSingleton as binhoSingleton
from .binhoHostAdapter import binhoDevice


class _binhoHostAdapterSingletonWrapper(object):

    """
    Convenience function that acts like binhoHostAdapterSingleton, but also allows Magic:
    accessing a property on this object will act as though that property had been
    accessed on a result of a binhoHostAdapterSingleton() call.
    That's heckin' unreadable, so in short-- accessing a property on a relevant object
    will attempt to 1) call the property on the sanest existing Binho object; or
    2) create a new Binho object, if necessary.
    """

    def __init__(self, serial=None):
        self.serial = serial

    def __getitem__(self, serial):
        return _binhoHostAdapterSingletonWrapper(serial)

    def __getattr__(self, name):
        return getattr(binhoSingleton(self.serial), name)

    def __call__(self, serial=None):
        return binhoSingleton(serial)

    def __dir__(self):
        return dir(binhoSingleton(self.serial))


binhoHostAdapterSingleton = _binhoHostAdapterSingletonWrapper()
