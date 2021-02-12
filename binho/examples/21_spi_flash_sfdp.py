import sys
import errno
from serial import SerialException

# import the binho library
from binho import binhoHostAdapter

# These imports help us handle errors gracefully
from binho.errors import DeviceNotFoundError

# Included for demonstrating the various ways to find and connect to Binho host adapters
# be sure to change them to match you device ID / comport
targetComport = "COM3"
targetDeviceID = "0x1c4780b050515950362e3120ff141c2a"

# Start by finding the desired host adapter and connecting to it
# wrap this with try/except to elegantly capture any connection errors
try:

    # grab the first device found the system finds
    binho = binhoHostAdapter()

    # When working with multiple host adapters connected to the same system
    # you can use any of the following methods to connect:

    # 1) grab the device with a specific index
    # binho = binhoHostAdapter(index=0)

    # 2) or get the device using the COM port
    # binho = binhoHostAdapter(port=targetComport)

    # 3) or get the device using the deviceID number
    # binho = binhoHostAdapter(deviceID = targetDeviceID)

except SerialException:

    print(
        "The target Binho host adapter was found, but failed to connect because another application already has an open\
         connection to it.",
        file=sys.stderr,
    )
    print(
        "Please close the connection in the other application and try again.", file=sys.stderr,
    )
    sys.exit(errno.ENODEV)

except DeviceNotFoundError:

    print(
        "No Binho host adapter found on serial port '{}'.".format(targetComport), file=sys.stderr,
    )
    sys.exit(errno.ENODEV)


# Once we made it this for, the connection to the device is open.
# wrap this with try/except to elegantly capture any errors and manage closing the
# connection to the host adapter automatically
try:

    print("Connected to a {} (deviceID: {}) on {}".format(binho.productName, binho.deviceID, binho.commPort))

    # set the host adapter operationMode to 'SPI'
    binho.operationMode = "SPI"

    # Let's explore which pins are available for use as CS pins
    # when we're in SPI mode
    pins = binho.gpio.getAvailablePins()
    print("List of available Pins:")

    for pin in pins:
        print(pin)

    print()

    # Let's grab the first available pin (IO0) to use as cs
    # look at the digitalIO example for more info about working with digital
    # IO pins
    csPinName = pins[0]
    csPin = binho.gpio.getPin(csPinName)

    # Additionally, most CS pins are active low, however if you want the CS pin
    # to operate as an active high signal, you can mark it as inverted
    # invertCS = True
    invertCS = False

    # Display the Default SPI configuration
    print("Default SPI bus configuration:")
    print(
        "Mode: {}, Clk Freq: {} Hz, Bit Order: {}, Bits per Transfer: {}".format(
            binho.spi.mode, binho.spi.frequency, binho.spi.bitOrder, binho.spi.bitsPerTransfer,
        )
    )
    print("CSPin: {}, Inverted: {}".format(csPin.pinName, str(invertCS)))
    print()

    # Now that we've got the SPI CS pin configuration, let's go ahead and create the programmer object
    # This function accepts a number of parameters, not all shown or demo'd here
    spiFlash = binho.create_programmer("spiFlash", chip_select_pin=csPin, autodetect=True, mode=0)

    # Let's see how much we can learn about the device without any prior knowledge
    # We can do this by first reading the Flash JEDEC ID and checking if it
    # supports SFDP (Serial Flash Discoverable Parameters)
    # SFDP standard is defined in JESD216 (https://www.jedec.org/standards-documents/docs/jesd216b)
    # and is freely available after creating a free login on the above website. Additionally,
    # some manufacturers have released App Notes with SDPF information for their Flash ICs.
    print(
        "JEDEC_ID: {}, Manufacturer: {}, Part Number: {}, Capacity: {} Kbit".format(
            hex(spiFlash.jedecID), spiFlash.manufacturer, spiFlash.mem_partNumber, spiFlash.capacity / 1024,
        )
    )

    deviceSupportForSFDP = spiFlash.supportsSFDP
    print("Supports SFDP: {}".format(deviceSupportForSFDP))
    print()

    # if the device supports SFDP, print out the parameter table
    # Note that the values printed are the raw values read out from the Flash
    # Reference the SFDP specification document linked above to understand how
    # to interpret the values into meaningful data.

    if deviceSupportForSFDP:

        print("Discovered parameters:")
        for param, value in spiFlash.parameterTable.items():
            print("{}: {}".format(param, value))

    else:

        print("Flash IC does not support SFDP! Giving up!")


# It's generally bad practice to indiscriminately catch all exceptions, however the
# binho_error_handler() simply prints out all the debug info as the script terminates
# it does not try to continue execution under any circumstances
except Exception:

    # Catch any exception that was raised and display it
    binho_error_hander()

finally:

    # close the connection to the host adapter
    binho.close()
