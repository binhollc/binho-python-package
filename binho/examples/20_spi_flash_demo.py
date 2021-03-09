import sys
import errno
from serial import SerialException
from intelhex import IntelHex

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

    if binho.inBootloaderMode:
        print(
            "{} found on {}, but it cannot be used now because it's in DFU mode".format(
                binho.productName, binho.commPort
            )
        )
        sys.exit(errno.ENODEV)

    elif binho.inDAPLinkMode:
        print(
            "{} found on {}, but it cannot be used now because it's in DAPlink mode".format(
                binho.productName, binho.commPort
            )
        )
        print("Tip: Exit DAPLink mode using 'binho daplink -q' command")
        sys.exit(errno.ENODEV)

    else:
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
    csPin = binho.IO0

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

    print("CSPin: {}, Inverted: {}".format(csPin.pin_name, str(invertCS)))
    print()

    # Now that we've got the SPI CS pin configuration, let's go ahead and create the programmer object
    # This function accepts a number of parameters, not all shown or demo'd here
    spiFlash = binho.create_programmer(
        "spiFlash", chip_select_pin=csPin, autodetect=True, mode=0, clocK_frequency=12000000,
    )

    # Notice we increased the clock frequency to 12MHz to make this quick

    # Let's see how much we can learn about the device without any prior knowledge
    # We can do this by first reading the Flash JEDEC ID and checking if it
    # supports SFDP (Serial Flash Discoverable Parameters)
    print(
        "JEDEC_ID: {}, Manufacturer: {}, Part Number: {}, Capacity: {} Kbits".format(
            hex(spiFlash.jedecID), spiFlash.manufacturer, spiFlash.mem_partNumber, spiFlash.capacity / 1024,
        )
    )

    deviceSupportForSFDP = spiFlash.supportsSFDP
    print("Supports SFDP: {}".format(deviceSupportForSFDP))
    print()

    # if the device supports SFDP, print out the parameter table
    if deviceSupportForSFDP:

        print("Discovered parameters:")
        print(
            "Capacity: {} bytes, Page Size: {} bytes, Page Count: {}".format(
                spiFlash.capacityBytes, spiFlash.pageSizeBytes, spiFlash.pageCount
            )
        )
    # See the 21_spi_flash_sfdp.py example to explore the full capability of SFDP

    # Let's read a byte
    address = 0x000000
    rxByte = spiFlash.readByte(address)
    print("Read a Byte @ address {}. Value = {}".format(address, hex(rxByte)))

    # Let's read a page
    print("Reading a page of data:")
    page_size = 256
    rxBytes = spiFlash.readBytes(address, page_size)
    print("Read byte count: {}".format(len(rxBytes)))

    print("offset", end="\t")
    for k in range(8):
        print(" {}".format(k), end="\t")
    print()

    for i in range(page_size // 8):
        print(hex(address + 8 * i), end="\t")
        for j in range(8):
            print(hex(rxBytes[i * 8 + j]), end="\t")
        print()

    # Let's read 1KB
    rxBytes = spiFlash.readBytes(address, 1024)
    print("length: {}".format(len(rxBytes)))

    # Let's read a non-integer multiple of pages
    rxBytes = spiFlash.readBytes(address, 3000)
    print("length: {}".format(len(rxBytes)))

    ## Lets write a page
    pageData = [0xDE, 0xAD, 0xBE, 0xEF]
    spiFlash.pageProgram(address, pageData)

    # Erasing is important too -- this is commented out so it doesn't accidentally
    # erase anyone's flash memory while trying out this demo.
    spiFlash.chipErase()

    # Let's read all the data
    # max_bytes = 16384 * 1024
    # rxBytes = spiFlash.readBytes(
    #    address, max_bytes
    # )
    # print("length: {}".format(len(rxBytes)))

finally:

    # close the connection to the host adapter
    binho.close()
