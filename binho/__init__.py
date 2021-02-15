from __future__ import print_function

import os

from .version import __version__

# Alias objects to make them easier to import.
from .binhoHostAdapter import binhoHostAdapter
from .binhoHostAdapter import binhoHostAdapterSingleton as binhoSingleton
from .binhoHostAdapter import binhoDevice


class _binhoHostAdapterSingletonWrapper:

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


def binho_assets_directory():
    """ Provide a quick function that helps us get at our assets directory. """

    # Find the path to the module, and then find its assets folder.
    module_path = os.path.dirname(__file__)
    return os.path.join(module_path, "assets")


def find_binho_asset(filename):
    """ Returns the path to a given Binho asset, if it exists, or None if the Binho asset isn't provided."""
    asset_path = os.path.join(binho_assets_directory(), filename)

    if os.path.isfile(asset_path):
        return asset_path

    return None
