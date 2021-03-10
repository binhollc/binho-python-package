from ..errors import DeviceError
from ..programmer import binhoProgrammer
from ..util.register import register

# from .firmware import DeviceFirmwareManager


def create_programmer(board, *args, **kwargs):
    """ Creates a representative programmer for the given module. """

    # For now, always create an SSPI interface.
    # We can take an 'interface' argument later to differentiate.
    return SPIFlash(board, *args, **kwargs)


# class SPIFlash(DeviceFirmwareManager, binhoProgrammer):
class SPIFlash(binhoProgrammer):
    """ Class representing an SPI flash connected to the Binho Host Adapter. """

    #
    # Common JEDEC manufacturer IDs for SPI flash chips.
    #
    JEDEC_MANUFACTURERS = {
        0xFF: "unknown",
        0x01: "AMD/Spansion/Cypress",
        0x04: "Fujitsu",
        0x1C: "eON",
        0x1F: "Atmel/Microchip",
        0x20: "Micron/Numonyx/ST",
        0x37: "AMIC",
        0x62: "SANYO",
        0x89: "Intel",
        0x8C: "ESMT",
        0xA1: "Fudan",
        0xAD: "Hyundai",
        0xBF: "SST",
        0xC2: "Micronix",
        0xC8: "Gigadevice",
        0xD5: "ISSI",
        0xEF: "Winbond",
        0xE0: "Paragon",
    }

    #
    # Common JEDEC device IDs. Prefixed with their manufacturer for easy / unique lookup.
    #
    JEDEC_PARTS = {
        0xFFFFFF: "unknown part",
        0xEF3015: "W25X16L",
        0xEF3014: "W25X80L",
        0xEF3013: "W25X40L",
        0xEF3012: "W25X20L",
        0xEF3011: "W25X10L",
        0xEF4015: "W25Q16DV",
        0xEF4018: "W25Q128FV",
        0xC22515: "MX25L1635E",
        0xC22017: "MX25L6405D",
        0xC22016: "MX25L3205D",
        0xC22015: "MX25L1605D",
        0xC22014: "MX25L8005",
        0xC22013: "MX25L4005",
        0xC22010: "MX25L512E",
        0x204011: "M45PE10",
        0x202014: "M25P80",
        0x1F4501: "AT24DF081",
        0x1C3114: "EN25F80",
        0xE04014: "PN25F08",
    }

    #
    # Common JEDEC capacity values.
    #
    JEDEC_CAPACITIES = {
        0x18: 0x1000000,
        0x17: 0x800000,
        0x16: 0x400000,
        0x15: 0x200000,
        0x14: 0x100000,
        0x13: 0x080000,
        0x12: 0x040000,
        0x11: 0x020000,
        0x10: 0x010000,
    }

    @property
    def jedecID(self):

        jedecID = self.board.spi.transfer([0x9F], 4, chip_select=self.csPin)

        jedecID = jedecID[1:4]

        if jedecID[0] in self.JEDEC_MANUFACTURERS:
            self.mem_manufacturer = self.JEDEC_MANUFACTURERS[jedecID[0]]
        else:
            self.mem_manufacturer = "Unrecognized Manufacturer"

        if jedecID[2] in self.JEDEC_CAPACITIES:
            self.mem_capacity = self.JEDEC_CAPACITIES[jedecID[2]]
        else:
            self.mem_capacity = 0

        jedecIDnumber = (jedecID[0] << 16) + (jedecID[1] << 8) + jedecID[2]

        if jedecIDnumber in self.JEDEC_PARTS:
            self.mem_partNumber = self.JEDEC_PARTS[jedecIDnumber]
        else:
            self.mem_partNumber = "Unrecognized Part"

        return jedecIDnumber

    @property
    def manufacturer(self):

        if not self.mem_manufacturer:

            jedecID = self.jedecID()

            if jedecID[0] in self.JEDEC_MANUFACTURERS:
                self.mem_manufacturer = self.JEDEC_MANUFACTURERS[jedecID[0]]
            else:
                self.mem_manufacturer = "Unrecognized Manufacturer"

        return self.mem_manufacturer

    @property
    def capacity(self):

        if not self.mem_capacity:

            jedecID = self.jedecID()

            if jedecID[2] in self.JEDEC_CAPACITIES:
                self.mem_capacity = self.JEDEC_CAPACITIES[jedecID[2]]
            else:
                self.mem_capacity = 0

        return self.mem_capacity

    @property
    def partNumber(self):

        if not self.mem_partNumber:

            jedecID = self.jedecID()

            jedecIDnumber = (jedecID[0] << 16) + (jedecID[1] << 8) + jedecID[2]

            if jedecIDnumber in self.JEDEC_PARTS:
                self.mem_partNumber = self.JEDEC_PARTS[jedecIDnumber]
            else:
                self.mem_partNumber = "Unrecognized Part"

        return self.mem_partNumber

    @property
    def supportsSFDP(self):

        is_supported = False

        try:

            rxData = self.board.spi.transfer([0x5A], 9, chip_select=self.csPin)
            is_supported = bool(rxData[5] == 0x53 and rxData[6] == 0x46 and rxData[7] == 0x44 and rxData[8] == 0x50)
            return is_supported

        except Exception:  # pylint: disable=broad-except

            return False

    def readSFPDParameterTable(self, baseAddress, length):

        tableData = self.readSFDPData(baseAddress, length)

        return tableData

    def readSFPDBasicFlashParameterTable(self, baseAddress):

        tableData = self.readSFDPData(baseAddress, 20 * 4)

        paramRegisters = []

        for i in range(20):

            value = (
                (tableData[i * 4 + 3] << 24)
                + (tableData[i * 4 + 2] << 16)
                + (tableData[i * 4 + 1] << 8)
                + tableData[i * 4]
            )

            paramRegisters.append(register(value, 32))

        # for i in range(len(paramTableDWORD)):
        #    print("DWORD-{}: {}".format(i, paramTableDWORD[i]))

        paramTable = {}

        # See JEDEC Standard No. 216D.01 (free, but registration required) for meanings of values
        # # https://www.jedec.org/document_search?search_api_views_fulltext=JEDEC+Standard+No.+216

        # 1st DWORD
        paramTable["SUPPORTS_1-1-4_FAST_READ"] = paramRegisters[0].getBit(22)
        paramTable["SUPPORTS_1-4-4_FAST_READ"] = paramRegisters[0].getBit(21)
        paramTable["SUPPORTS_1-2-2_FAST_READ"] = paramRegisters[0].getBit(20)
        paramTable["SUPPORTS_DTR_CLOCKING"] = paramRegisters[0].getBit(19)
        paramTable["ADDRESS_BYTES"] = paramRegisters[0].getBits(17, 18)
        paramTable["SUPPORTS_1-1-2_FAST_READ"] = paramRegisters[0].getBit(16)
        paramTable["4KB_ERASE_INSTRUCTION"] = paramRegisters[0].getBits(8, 15)
        paramTable["WRITE_ENABLE_INSTRUCTION_SELECT"] = paramRegisters[0].getBit(4)
        paramTable["VOLATILE_STATUS_REGISTER_BLOCK_PROTECT_BITS"] = paramRegisters[0].getBit(3)
        paramTable["WRITE_GRANULARITY"] = paramRegisters[0].getBit(2)
        paramTable["BLOCK_ERASE_SIZES"] = paramRegisters[0].getBits(0, 1)

        # 2nd DWORD
        paramTable["FLASH_MEMORY_DENSITY"] = paramRegisters[1].value

        # 3rd DWORD
        paramTable["1-1-4_FAST_READ_INSTRUCTION"] = paramRegisters[2].getBits(24, 31)
        paramTable["1-1-4_FAST_READ_NUM_MODE_CLOCKS"] = paramRegisters[2].getBits(21, 23)
        paramTable["1-1-4_FAST_READ_NUM_WAITS"] = paramRegisters[2].getBits(16, 20)
        paramTable["1-4-4_FAST_READ_INSTRUCTION"] = paramRegisters[2].getBits(8, 15)
        paramTable["1-4-4_FAST_READ_NUM_MODE_CLOCKS"] = paramRegisters[2].getBits(5, 7)
        paramTable["1-4-4_FAST_READ_NUM_WAITS"] = paramRegisters[2].getBits(0, 4)

        # 4th DWORD
        paramTable["1-2-2_FAST_READ_INSTRUCTION"] = paramRegisters[3].getBits(24, 31)
        paramTable["1-2-2_FAST_READ_NUM_MODE_CLOCKS"] = paramRegisters[3].getBits(21, 23)
        paramTable["1-2-2_FAST_READ_NUM_WAITS"] = paramRegisters[3].getBits(16, 20)
        paramTable["1-1-2_FAST_READ_INSTRUCTION"] = paramRegisters[3].getBits(8, 15)
        paramTable["1-1-2_FAST_READ_NUM_MODE_CLOCKS"] = paramRegisters[3].getBits(5, 7)
        paramTable["1-1-2_FAST_READ_NUM_WAITS"] = paramRegisters[3].getBits(0, 4)

        # 5th DWORD
        paramTable["SUPPORTS_4-4-4_FAST_READ"] = paramRegisters[4].getBit(4)
        paramTable["SUPPORTS_2-2-2_FAST_READ"] = paramRegisters[4].getBit(0)

        # 6th DWORD
        paramTable["2-2-2_FAST_READ_INSTRUCTION"] = paramRegisters[5].getBits(24, 31)
        paramTable["2-2-2_FAST_READ_NUM_MODE_CLOCKS"] = paramRegisters[5].getBits(21, 23)
        paramTable["2-2-2_FAST_READ_NUM_WAITS"] = paramRegisters[5].getBits(16, 20)

        # 7th DWORD
        paramTable["4-4-4_FAST_READ_INSTRUCTION"] = paramRegisters[6].getBits(24, 31)
        paramTable["4-4-4_FAST_READ_NUM_MODE_CLOCKS"] = paramRegisters[6].getBits(21, 23)
        paramTable["4-4-4_FAST_READ_NUM_WAITS"] = paramRegisters[6].getBits(16, 20)

        # 8th DWORD
        paramTable["ERASE_TYPE_2_INSTRUCTION"] = paramRegisters[7].getBits(24, 31)
        paramTable["ERASE_TYPE_2_SIZE"] = paramRegisters[7].getBits(16, 23)
        paramTable["ERASE_TYPE_1_INSTRUCTION"] = paramRegisters[7].getBits(8, 15)
        paramTable["ERASE_TYPE_1_SIZE"] = paramRegisters[7].getBits(0, 7)

        # 9th DWORD
        paramTable["ERASE_TYPE_4_INSTRUCTION"] = paramRegisters[8].getBits(24, 31)
        paramTable["ERASE_TYPE_4_SIZE"] = paramRegisters[8].getBits(16, 23)
        paramTable["ERASE_TYPE_3_INSTRUCTION"] = paramRegisters[8].getBits(8, 15)
        paramTable["ERASE_TYPE_3_SIZE"] = paramRegisters[8].getBits(0, 7)

        # 10th DWORD
        paramTable["ERASE_TYPE_4_TYPICAL_TIME"] = paramRegisters[9].getBits(25, 31)
        paramTable["ERASE_TYPE_3_TYPICAL_TIME"] = paramRegisters[9].getBits(18, 24)
        paramTable["ERASE_TYPE_2_TYPICAL_TIME"] = paramRegisters[9].getBits(11, 17)
        paramTable["ERASE_TYPE_1_TYPICAL_TIME"] = paramRegisters[9].getBits(4, 10)
        paramTable["ERASE_MULTIPLIER_FROM_TYPICAL_TIME_TO_MAX"] = paramRegisters[9].getBits(0, 3)

        # 11th DWORD
        paramTable["CHIP_ERASE_TYPICAL_TIME"] = paramRegisters[10].getBits(24, 30)
        paramTable["BYTE_PROGRAM_TYPICAL_TIME_ADDITIONAL"] = paramRegisters[10].getBits(19, 23)
        paramTable["BYTE_PROGRAM_TYPICAL_TIME_FIRST_BYTE"] = paramRegisters[10].getBits(14, 18)
        paramTable["PAGE_PROGRAM_TYPICAL_TIME"] = paramRegisters[10].getBits(8, 13)
        paramTable["PAGE_SIZE"] = paramRegisters[10].getBits(4, 7)
        paramTable["PAGE_BYTE_PROGRAM_MULTIPLIER_FROM_TYPICAL_TIME_TO_MAX"] = paramRegisters[10].getBits(0, 3)

        # 12th DWORD
        paramTable["SUSPEND_RESUME_SUPPORTED"] = paramRegisters[11].getBit(31)
        paramTable["SUSPEND_INPROG_ERASE_MAX_LATENCY"] = paramRegisters[11].getBits(24, 30)
        paramTable["ERASE_RESUME_TO_SUSPEND_INTERVAL"] = paramRegisters[11].getBits(20, 23)
        paramTable["SUSPEND_INPROG_PROGRAM_MAX_LATENCY"] = paramRegisters[11].getBits(13, 19)
        paramTable["PROGRAM_RESUME_TO_SUSPEND_INTERVAL"] = paramRegisters[11].getBits(9, 12)
        paramTable["PROHIBITED_OPS_DURING_ERASE_SUSPEND"] = paramRegisters[11].getBits(4, 7)
        paramTable["PROHIBITED_OPS_DURING_PROGRAM_SUSPEND"] = paramRegisters[11].getBits(0, 3)

        # 13th DWORD
        paramTable["SUSPEND_INSTRUCTION"] = paramRegisters[12].getBits(24, 31)
        paramTable["RESUME_INSTRUCTION"] = paramRegisters[12].getBits(16, 23)
        paramTable["PROGRAM_SUSPEND_INSTRUCTION"] = paramRegisters[12].getBits(8, 15)
        paramTable["PROGRAM_RESUME_INSTRUCTION"] = paramRegisters[12].getBits(0, 7)

        # 14th DWORD
        paramTable["DEEP_POWERDOWN_SUPPORTED"] = paramRegisters[13].getBit(31)
        paramTable["ENTER_DEEP_POWERDOWN_INSTRUCTION"] = paramRegisters[13].getBits(23, 30)
        paramTable["EXIT_DEEP_POWERDOWN_INSTRUCTION"] = paramRegisters[13].getBits(15, 22)
        paramTable["EXIT_DEEP_POWERDOWN_TO_NEXT_OP_DELAY"] = paramRegisters[13].getBits(8, 14)
        paramTable["STATUS_REGISTER_POLLING_DEVICE_BUSY"] = paramRegisters[13].getBits(2, 7)

        # 15th DWORD
        paramTable["HOLD_OR_RESET_DISABLE"] = paramRegisters[14].getBit(23)
        paramTable["QUAD_ENABLE_REQUIREMENTS"] = paramRegisters[14].getBits(20, 22)
        paramTable["0-4-4_MODE_ENTRY_METHOD"] = paramRegisters[14].getBits(16, 19)
        paramTable["0-4-4_MODE_EXIT_METHOD"] = paramRegisters[14].getBits(10, 15)
        paramTable["0-4-4_MODE_SUPPORTED"] = paramRegisters[14].getBit(9)
        paramTable["4-4-4_MODE_ENABLE_SEQUENCES"] = paramRegisters[14].getBits(4, 8)
        paramTable["4-4-4_MODE_DISABLE_SEQUENCES"] = paramRegisters[14].getBits(0, 3)

        # 16th DWORD
        paramTable["ENTER_4BYTE_ADDRESSING"] = paramRegisters[15].getBits(24, 31)
        paramTable["EXIT_4BYTE_ADDRESSING"] = paramRegisters[15].getBits(14, 23)
        paramTable["SOFT_RESET_AND_RESCUE_SEQ_SUPPORT"] = paramRegisters[15].getBits(8, 13)
        paramTable["VOLATILE_OR_NV_REGISTER_AND_WE_INSTRUCTION_STATUSREG1"] = paramRegisters[15].getBits(0, 6)

        # 17th DWORD
        paramTable["1-1-8_FAST_READ_INSTRUCTION"] = paramRegisters[16].getBits(24, 31)
        paramTable["1-1-8_FAST_READ_NUM_MODE_CLOCKS"] = paramRegisters[16].getBits(21, 23)
        paramTable["1-1-8_FAST_READ_NUM_WAITS"] = paramRegisters[16].getBits(16, 20)
        paramTable["1-8-8_FAST_READ_INSTRUCTION"] = paramRegisters[16].getBits(8, 15)
        paramTable["1-8-8_FAST_READ_NUM_MODE_CLOCKS"] = paramRegisters[16].getBits(5, 7)
        paramTable["1-8-8_FAST_READ_NUM_WAITS"] = paramRegisters[16].getBits(0, 4)

        # 18th DWORD
        paramTable["BYTE_ORDER_IN_8D-8D-8D_MODE"] = paramRegisters[17].getBit(31)
        paramTable["8D-8D-8D_COMMAND_AND_CMD_EXTENSION"] = paramRegisters[17].getBits(29, 30)
        paramTable["DATA_STROBE_SUPPORT_FOR_QPI_DTR_MODE"] = paramRegisters[17].getBit(27)
        paramTable["DATA_STROBE_SUPPORT_FOR_QPI_STR_MODE"] = paramRegisters[17].getBit(26)
        paramTable["DATA_STROBE_WAVEFORMS_IN_STR_MODE"] = paramRegisters[17].getBits(24, 25)
        paramTable["JEDEC_SPI_PROTOCOL_RESET"] = paramRegisters[17].getBit(23)
        paramTable["VARIABLE_OUTPUT_DRIVER_STRENGTH"] = paramRegisters[17].getBits(18, 22)

        # 19th DWORD
        paramTable["OCTAL_ENABLE_REQUIREMENTS"] = paramRegisters[18].getBits(20, 22)
        paramTable["0-8-8_MODE_ENTRY_METHOD"] = paramRegisters[18].getBits(16, 19)
        paramTable["0-8-8_MODE_EXIT_METHOD"] = paramRegisters[18].getBits(10, 15)
        paramTable["0-8-8_MODE_SUPPORTED"] = paramRegisters[18].getBit(9)
        paramTable["8S-8S-8S_MODE_ENABLE_SEQUENCES"] = paramRegisters[18].getBits(4, 8)
        paramTable["8S-8S-8S_MODE_DISABLE_SEQUENCES"] = paramRegisters[18].getBits(0, 3)

        # 20th DWORD
        paramTable["MAX_OP_SPEED_8D-8D-8D-WITH_STROBE"] = paramRegisters[19].getBits(28, 31)
        paramTable["MAX_OP_SPEED_8D-8D-8D-NO_STROBE"] = paramRegisters[19].getBits(24, 27)

        paramTable["MAX_OP_SPEED_8S-8S-8S-WITH_STROBE"] = paramRegisters[19].getBits(20, 23)
        paramTable["MAX_OP_SPEED_8S-8S-8S-NO_STROBE"] = paramRegisters[19].getBits(16, 19)

        paramTable["MAX_OP_SPEED_4S-4D-4D-WITH_STROBE"] = paramRegisters[19].getBits(12, 15)
        paramTable["MAX_OP_SPEED_4S-4D-4D-NO_STROBE"] = paramRegisters[19].getBits(8, 11)

        paramTable["MAX_OP_SPEED_4S-4S-4S-WITH_STROBE"] = paramRegisters[19].getBits(4, 7)
        paramTable["MAX_OP_SPEED_4S-4S-4S-NO_STROBE"] = paramRegisters[19].getBits(0, 3)

        return paramTable

    def getNumberOfSFPDHeaders(self):

        data = self.readSFDPData(0x06, 1)
        numberOfParameterHeaders = data[0] + 1

        return numberOfParameterHeaders

    def readSFPDParameterHeader(self, baseAddress):

        headerData = self.readSFDPData(baseAddress, 8)

        paramHeader = {}
        paramHeader["PARAMETERID_LSB"] = headerData[0]
        paramHeader["PARAMETER_MINOR_REV"] = headerData[1]
        paramHeader["PARAMETER_MAJOR_REV"] = headerData[2]
        paramHeader["PARAMETER_LENGTH_DWORDS"] = headerData[3]
        paramHeader["PARAMETER_TABLE_POINTER"] = (headerData[6] << 16) + (headerData[5] << 8) + headerData[4]
        paramHeader["PARAMETERID_MSB"] = headerData[7]

        return paramHeader

    def readSFDPData(self, address, bytesToRead):
        addr = [0x00, 0x00, 0x00]
        addr[0] = (address >> 16) & 0xFF
        addr[1] = (address >> 8) & 0xFF
        addr[2] = address & 0xFF

        txData = [0x5A] + addr + [0x00]

        rxData = self.board.spi.transfer(txData, len(txData) + bytesToRead, chip_select=self.csPin)

        return rxData[5 : bytesToRead + 5]

    def readUniqueIDNumber(self):

        txData = [0x4B] + [0x00, 0x00, 0x00, 0x00]

        rxData = self.board.spi.transfer(txData, len(txData) + 8, chip_select=self.csPin)

        return rxData[5:13]

    def reset(self):

        # Enable Reset
        txData = [0x66]
        self.board.spi.transfer(txData, len(txData), chip_select=self.csPin)

        # Reset Device
        txData = [0x99]
        self.board.spi.transfer(txData, len(txData), chip_select=self.csPin)

        return True

    def readByte(self, address):

        addr = [0x00, 0x00, 0x00]
        addr[0] = (address >> 16) & 0xFF
        addr[1] = (address >> 8) & 0xFF
        addr[2] = address & 0xFF

        txData = [0x03] + addr

        rxData = self.board.spi.transfer(txData, len(txData) + 1, chip_select=self.csPin)

        return rxData[4]

    def readBytes(self, startingAddress, bytesToRead):

        addr = [0x00, 0x00, 0x00]
        baseAddress = startingAddress
        bytesRemaining = bytesToRead
        rxData = []

        while bytesRemaining > 0:

            if bytesRemaining > 1020:

                addr[0] = (baseAddress >> 16) & 0xFF
                addr[1] = (baseAddress >> 8) & 0xFF
                addr[2] = baseAddress & 0xFF

                txData = [0x03] + addr

                data = self.board.spi.transfer(
                    txData, len(txData) + 1020, chip_select=self.csPin, deassert_chip_select=False,
                )
                rxData += data[4:1024]
                bytesRemaining = bytesRemaining - 1020
                baseAddress += 1020

            else:

                addr[0] = (baseAddress >> 16) & 0xFF
                addr[1] = (baseAddress >> 8) & 0xFF
                addr[2] = baseAddress & 0xFF

                txData = [0x03] + addr

                data = self.board.spi.transfer(txData, len(txData) + bytesRemaining, chip_select=self.csPin)
                rxData += data[4 : bytesRemaining + 4]
                bytesRemaining = 0

        return rxData

    def pageProgram(self, startingAddress, dataBytes, blockUntilFinished=True):

        addr = [0x00, 0x00, 0x00]
        addr[0] = (startingAddress >> 16) & 0xFF
        addr[1] = (startingAddress >> 8) & 0xFF
        addr[2] = startingAddress & 0xFF

        txData = [0x02] + addr + dataBytes

        if self.isBusy():
            return False

        self.writeEnable()

        self.board.spi.transfer(txData, len(txData), chip_select=self.csPin)

        self._blockUntilFinished(blockUntilFinished)

        return True

    def writeEnable(self):

        txData = [0x06]
        self.board.spi.transfer(txData, len(txData), chip_select=self.csPin)

        return True

    def writeDisable(self):

        txData = [0x04]
        self.board.spi.transfer(txData, len(txData), chip_select=self.csPin)

        return True

    def readStatusRegister(self, statusRegister=1):

        if statusRegister == 3:
            txData = [0x15]
        elif statusRegister == 2:
            txData = [0x35]
        else:
            txData = [0x05]

        rxData = self.board.spi.transfer(txData, len(txData), chip_select=self.csPin)

        return rxData[0]

    def writeStatusRegister(self, value, statusRegister=1):

        if statusRegister == 3:
            txData = [0x11] + [value]
        elif statusRegister == 2:
            txData = [0x31] + [value]
        else:
            txData = [0x01] + [value]

        self.writeEnable()

        self.board.spi.transfer(txData, len(txData), chip_select=self.csPin)

        return True

    def isBusy(self):

        regVal = self.readStatusRegister()

        if regVal & 0x01 == 0:
            return False

        return True

    def eraseBlock(self, blockAddress, blockSizeKB=64, blockUntilFinished=True):

        addr = [0x00, 0x00, 0x00]
        addr[0] = (blockAddress >> 16) & 0xFF
        addr[1] = (blockAddress >> 8) & 0xFF
        addr[2] = blockAddress & 0xFF

        if blockSizeKB == 64:
            txData = [0xD8] + addr  # 64KB
        elif blockSizeKB == 32:
            txData = [0x52] + addr  # 32KB
        else:
            txData = [0x20] + addr

        if self.isBusy():
            return False

        self.writeEnable()

        self.board.spi.transfer(txData, len(txData), chip_select=self.csPin)

        self._blockUntilFinished(blockUntilFinished)

        return True

    def chipErase(self, blockUntilFinished=True):

        txData = [0xC7]

        if self.isBusy():
            return False

        self.writeEnable()

        self.board.spi.transfer(txData, len(txData), chip_select=self.csPin)

        self._blockUntilFinished(blockUntilFinished)

        return True

    def _blockUntilFinished(self, block=True):

        if block:
            busy = True
            while busy:
                busy = self.isBusy()

        return True

    @property
    def parameterTable(self):

        return self._paramTable

    @property
    def topologyTable(self):

        return self._deviceTopology

    @property
    def pageSizeBytes(self):

        return self._deviceTopology["PAGE_SIZE_BYTES"]

    @property
    def capacityBytes(self):

        return self._deviceTopology["TOTAL_SIZE_BYTES"]

    @property
    def pageCount(self):

        return self._deviceTopology["PAGE_COUNT"]

    def __init__(
        self,
        board,
        autodetect=True,
        allow_fallback=False,
        page_size=256,
        pages=8192,
        maximum_address=None,
        allow_null_jedec=False,
        device_id=0,
        chip_select_pin=None,
        clocK_frequency=2000000,
        mode=0,
        force_page_size=None,
    ):  # pylint: disable=too-many-arguments, too-many-locals, unused-argument
        """Set up a new SPI flash connection.
        Args:
            board -- The Binho Host Adapter that will be programming our flash chip.
            autodetect -- If True, the API will attempt to automatically detect the flash's parameters.
            allow_fallback -- If False, we'll fail if autodetect is set and we can't autodetect the flash's paramters.
                If true, we'll fall-back to the keyword arguments provided
        """

        # Store a reference to the parent board, via which we'll program the
        # the actual SPI flash.
        self.board = board

        self.csPin = chip_select_pin
        self.board.spi.mode = mode
        self.board.spi.frequency = clocK_frequency

        self.mem_manufacturer = None
        self.mem_capacity = None
        self.mem_partNumber = None

        self._paramTable = {}

        self._deviceTopology = {}
        self._deviceTopology["PAGE_SIZE_BYTES"] = page_size
        self._deviceTopology["TOTAL_SIZE_BYTES"] = page_size * pages
        self._deviceTopology["PAGE_COUNT"] = (
            self._deviceTopology["TOTAL_SIZE_BYTES"] / self._deviceTopology["PAGE_SIZE_BYTES"]
        )

        # If autodetect is set to True, we'll try to automatically detect
        # the device's topology.
        if autodetect:

            if self.supportsSFDP:

                numberOfParameterHeaders = self.getNumberOfSFPDHeaders()

                for _ in range(numberOfParameterHeaders):

                    paramHeader = self.readSFPDParameterHeader(0x08)

                    if paramHeader["PARAMETERID_LSB"] == 0x00 and paramHeader["PARAMETERID_MSB"] == 0xFF:

                        self._paramTable = self.readSFPDBasicFlashParameterTable(paramHeader["PARAMETER_TABLE_POINTER"])

                        self._deviceTopology["PAGE_SIZE_BYTES"] = 2 ** self._paramTable["PAGE_SIZE"]
                        self._deviceTopology["TOTAL_SIZE_BYTES"] = (self._paramTable["FLASH_MEMORY_DENSITY"] + 1) / 8
                        self._deviceTopology["PAGE_COUNT"] = (
                            self._deviceTopology["TOTAL_SIZE_BYTES"] / self._deviceTopology["PAGE_SIZE_BYTES"]
                        )

                    else:
                        if not allow_fallback:
                            raise DeviceError(
                                "Could not read SFDP on connected device & Fallback is disabled! Giving Up!"
                            )

            else:
                if not allow_fallback:
                    raise DeviceError("Could not read SFDP on connected device & Fallback is disabled! Giving Up!")
