class register:
    def __init__(self, initialValue=0x00, widthInBits=8, name="Unnamed Register"):

        self.name = name
        self.widthInBits = widthInBits
        self.value = initialValue

    def getBit(self, bitNumber):
        bitVal = (self.value & (1 << bitNumber)) >> bitNumber
        return bitVal

    def getBits(self, staringfromBit, upToIncludingBit):

        bitMask = 0

        for _ in range((upToIncludingBit - staringfromBit) + 1):
            bitMask = (bitMask << 1) + 1

        bitMask = bitMask << staringfromBit

        bitsVal = (self.value & bitMask) >> staringfromBit

        return bitsVal
