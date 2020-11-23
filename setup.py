import os
import sys
from setuptools import setup, find_packages


def read(fname):
    filename = os.path.join(os.path.dirname(__file__), fname)
    with open(filename, "r") as f:
        return f.read()


# Handle python2 vs python3 requirements.
per_version_requirements = []
if sys.version_info < (3, 0):
    per_version_requirements.append("ipython<6")
else:
    per_version_requirements.append("ipython")


setup_req = []
setup_options = {}

# Deduce version, if possible.
if os.path.isfile("../VERSION"):
    setup_options["version"] = read("../VERSION").strip()
else:
    setup_options["version_config"] = {
        "version_format": "{tag}.dev+git.{sha}",
        "starting_version": "2020.10.05",
    }
    setup_req.append("even-better-setuptools-git-version")

setup(
    name="binho",
    setup_requires=setup_req,
    url="https://binho.io",
    license="BSD",
    entry_points={
        "console_scripts": [
            "binhoHostAdapter = binho.commands.binho:main",
            "binho = binho.commands.binho:main",
            "binho_shell = binho.commands.binho_shell:main",
            "binho_info = binho.commands.binho_info:main",
            "binho_uart = binho.commands.binho_uart:main",
            "binho_i2c = binho.commands.binho_i2c:main",
            "binho_spi = binho.commands.binho_spi:main",
            "binho_spiflash = binho.commands.binho_spiflash:main",
            "binho_1wire = binho.commands.binho_1wire:main",
            "binho_oneWire = binho.commands.binho_1wire:main",
            "binho_adc = binho.commands.binho_adc:main",
            "binho_dac = binho.commands.binho_dac:main",
            "binho_gpio = binho.commands.binho_gpio:main",
            "binho_pwm = binho.commands.binho_pwm:main",
            "binho_eeprom = binho.commands.binho_eeprom:main",
            "binho_firmware = binho.commands.binho_firmware:main",
            "binho_dfu = binho.commands.binho_firmware:main",
        ],
    },
    author="Binho LLC",
    author_email="support@binho.io",
    install_requires=[
        per_version_requirements,
        "future",
        "tqdm",
        "tabulate",
        "intelhex",
        "prompt_toolkit<2.1.0",
        "pyserial"
    ],
    description="Python package for Binho USB host adapter products",
    long_description=read("README.md"),
    packages=find_packages(),
    include_package_data=True,
    platforms="any",
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 1 - Planning",
        "Natural Language :: English",
        "Environment :: Console",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
    ],
    extras_require={
        "dev": [
            "sphinx",
            "sphinx_rtd_theme",
        ]
    },
    **setup_options,
)
