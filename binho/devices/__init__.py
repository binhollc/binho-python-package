from os.path import dirname, basename, isfile
import glob

# Autodetect all devices in the  directory
modules = glob.glob(dirname(__file__) + "/*.py")
__all__ = [basename(f)[:-3] for f in modules if isfile(f)]
