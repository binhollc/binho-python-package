import os
import enum
import threading
import queue
import signal
import sys
import serial

from binho.errors import DeviceError

SERIAL_TIMEOUT = 0.5


class SerialPortManager(threading.Thread):

    serialPort = None
    txdQueue = None
    rxdQueue = None
    intQueue = None
    stopper = None
    inBridgeMode = False

    def __init__(self, serialPort, txdQueue, rxdQueue, intQueue, stopper):  # pylint: disable=too-many-arguments
        super().__init__()
        self.serialPort = serialPort
        self.txdQueue = txdQueue
        self.rxdQueue = rxdQueue
        self.intQueue = intQueue
        self.stopper = stopper
        self.exception = None
        self.daemon = True

    def _transceive(self, comport: serial.Serial) -> None:
        if self.inBridgeMode:

            if comport.in_waiting > 0:
                receivedData = comport.read().decode("utf-8")
                self.rxdQueue.put(receivedData)

            if not self.txdQueue.empty():
                serialData = self.txdQueue.get()
                comport.write(serialData.encode("utf-8"))
        else:

            if comport.in_waiting > 0:
                receivedData = comport.readline().strip().decode("utf-8")

                if len(receivedData) > 0:

                    if receivedData[0] == "!":
                        self.intQueue.put(receivedData)
                    elif receivedData[0] == "-":
                        self.rxdQueue.put(receivedData)

            if not self.txdQueue.empty():
                serialCommand = self.txdQueue.get() + "\n"
                comport.write(serialCommand.encode("utf-8"))

    def run(self):
        comport = None
        try:
            comport = serial.Serial(self.serialPort, baudrate=1000000, timeout=0.025, write_timeout=0.05)
            while not self.stopper.is_set():  # pylint: disable=too-many-nested-blocks
                self._transceive(comport)
        except Exception as e:  # pylint: disable=broad-except
            self.stopper.set()
            self.exception = e
            # print('Comm Error!')
        finally:
            if comport is not None:
                comport.close()

    def get_exception(self):
        return self.exception

    def startUartBridge(self):
        self.inBridgeMode = True

    def stopUartBridge(self):
        self.inBridgeMode = False


class SignalHandler:
    """
    The object that will handle signals and stop the worker threads.
    """

    #: The stop event that's shared by this handler and threads.
    stopper = None

    #: The pool of worker threads
    workers = None

    def __init__(self, stopper, manager):
        self.stopper = stopper
        self.manager = manager

    def __call__(self, signum, frame):
        """
        This will be called by the python signal module
        https://docs.python.org/3/library/signal.html#signal.signal
        """
        self.stopper.set()

        self.manager.join()

        sys.exit(0)

    def sendStop(self):

        self.stopper.set()

        self.manager.join()


class oneWireCmd(enum.Enum):
    """Enum for exchangeBytes1WIRE"""

    NONE = "NONE"
    SELECT = "SELECT"
    SKIP = "SKIP"


class binhoComms:
    def __init__(self, serialPort):

        self.serialPort = serialPort
        self.handler = None
        self.manager = None
        self.interrupts = None
        self._stopper = None
        self._txdQueue = None
        self._rxdQueue = None
        self._intQueue = None
        self._debug = os.getenv("BINHO_NOVA_DEBUG")

    # Destructor
    def __del__(self):

        if self.handler is not None:
            try:
                self.handler.sendStop()
            except Exception:  # pylint: disable=broad-except
                pass

    # Private functions

    def _checkInterrupts(self):

        while not self._intQueue.empty():
            self.interrupts.add(self._intQueue.get())

    # Public functions

    def sendCommand(self, command):
        if self._debug is not None:
            print(command)
        self._txdQueue.put(command, timeout=SERIAL_TIMEOUT)

    def readResponse(self):

        result = "[ERROR]"

        if self.manager.is_alive():
            if not self.manager.get_exception():
                try:
                    result = self._rxdQueue.get(timeout=SERIAL_TIMEOUT)
                except queue.Empty:
                    # print('Connection with Device Lost!')
                    self.handler.sendStop()
        else:
            # print('Connection with Device Lost!')
            self.handler.sendStop()

        if self._debug is not None:
            print(result)
        return result

    @classmethod
    def checkDeviceSuccess(cls, ret_str):
        if ret_str == "-OK":
            return True
        if ret_str == "-NG":
            return False

        raise DeviceError(f"Invalid command response: {ret_str}")

    # Communication Management

    def start(self):

        self.handler = None
        self.manager = None
        self.interrupts = None
        self._stopper = None
        self._txdQueue = None
        self._rxdQueue = None
        self._intQueue = None

        comport = serial.Serial(self.serialPort, baudrate=1000000, timeout=0.025, write_timeout=0.05)
        comport.close()

        self.interrupts = set()

        self._stopper = threading.Event()
        self._txdQueue = queue.Queue()
        self._rxdQueue = queue.Queue()
        self._intQueue = queue.Queue()

        # we need to keep track of the workers but not start them yet
        # workers = [StatusChecker(url_queue, result_queue, stopper) for i in range(num_workers)]
        self.manager = SerialPortManager(
            self.serialPort, self._txdQueue, self._rxdQueue, self._intQueue, self._stopper,
        )

        # create our signal handler and connect it
        self.handler = SignalHandler(self._stopper, self.manager)
        signal.signal(signal.SIGINT, self.handler)

        # start the threads!
        self.manager.daemon = True

        self.manager.start()

    def open(self):

        self.interrupts.clear()
        self.manager.start()

    def isConnected(self):

        return self.manager.is_alive()

    def isCommError(self):

        e = self.manager.get_exception()

        if e:
            return True

        return False

    def close(self):

        if self.handler:
            self.handler.sendStop()

    def interruptCount(self):

        self._checkInterrupts()

        return len(self.interrupts)

    def interruptCheck(self, interrupt):

        self._checkInterrupts()

        if interrupt in self.interrupts:
            return True

        return False

    def interruptClear(self, interrupt):

        self.interrupts.discard(interrupt)

    def interruptClearAll(self):

        self.interrupts.clear()

    def getInterrupts(self):

        self._checkInterrupts()

        return self.interrupts.copy()

    # BUFFER COMMANDS

    def clearBuffer(self, bufferIndex):

        self.sendCommand("BUF" + str(bufferIndex) + " CLEAR")
        result = self.readResponse()

        return result

    def addByteToBuffer(self, bufferIndex, value):

        self.sendCommand("BUF" + str(bufferIndex) + " ADD " + str(value))
        result = self.readResponse()

        return result

    def readBuffer(self, bufferIndex, numBytes):

        self.sendCommand("BUF" + str(bufferIndex) + " READ " + str(numBytes))
        result = self.readResponse()

        return result

    def writeToBuffer(self, bufferIndex, startIndex, data):

        bufferData = ""

        for x in data:
            bufferData += " " + str(x)

        self.sendCommand("BUF" + str(bufferIndex) + " WRITE " + str(startIndex) + bufferData)
        result = self.readResponse()

        return result

    # UART COMMANDS

    def setBaudRateUART(self, uartIndex, baud):

        self.sendCommand("UART" + str(uartIndex) + " BAUD " + str(baud))
        result = self.readResponse()

        return result

    def getBaudRateUART(self, uartIndex):

        self.sendCommand("UART" + str(uartIndex) + " BAUD ?")
        result = self.readResponse()

        return result

    def setDataBitsUART(self, uartIndex, databits):

        self.sendCommand("UART" + str(uartIndex) + " DATABITS " + str(databits))
        result = self.readResponse()

        return result

    def getDataBitsUART(self, uartIndex):

        self.sendCommand("UART" + str(uartIndex) + " DATABITS ?")
        result = self.readResponse()

        return result

    def setParityUART(self, uartIndex, parity):

        self.sendCommand("UART" + str(uartIndex) + " PARITY " + str(parity))
        result = self.readResponse()

        return result

    def getParityUART(self, uartIndex):

        self.sendCommand("UART" + str(uartIndex) + " PARITY ?")
        result = self.readResponse()

        return result

    def setStopBitsUART(self, uartIndex, stopbits):

        self.sendCommand("UART" + str(uartIndex) + " STOPBITS " + str(stopbits))
        result = self.readResponse()

        return result

    def getStopBitsUART(self, uartIndex):

        self.sendCommand("UART" + str(uartIndex) + " STOPBITS ?")
        result = self.readResponse()

        return result

    def setEscapeSequenceUART(self, uartIndex, escape):

        self.sendCommand("UART" + str(uartIndex) + " ESC " + escape)
        result = self.readResponse()

        return result

    def getEscapeSequenceUART(self, uartIndex):

        self.sendCommand("UART" + str(uartIndex) + " ESC ?")
        result = self.readResponse()

        return result

    def beginBridgeUART(self, uartIndex):

        self.sendCommand("UART" + str(uartIndex) + " BEGIN")
        result = self.readResponse()

        self.manager.startUartBridge()

        return result

    def stopBridgeUART(self, sequence):

        self.manager.stopUartBridge()
        self._txdQueue.put(sequence, timeout=SERIAL_TIMEOUT)
        result = self.readResponse()

        return result

    def writeBridgeUART(self, data):

        self._txdQueue.put(data, timeout=SERIAL_TIMEOUT)

    def readBridgeUART(self, timeout=SERIAL_TIMEOUT):
        # Don't raise an exception if there is nothing to read, the other side may hae nothing to say
        # But don't wait forever
        return self._rxdQueue.get(timeout=timeout)

    # SWI COMMANDS

    def beginSWI(self, swiIndex, pin, pullup):

        if not pullup:
            self.sendCommand("SWI" + str(swiIndex) + " BEGIN " + str(pin))
        else:
            self.sendCommand("SWI" + str(swiIndex) + " BEGIN " + str(pin) + " PULL")

        result = self.readResponse()

        return result

    def sendTokenSWI(self, swiIndex, token):

        self.sendCommand("SWI" + str(swiIndex) + " TOKEN " + str(token))
        result = self.readResponse()

        return result

    def sendFlagSWI(self, swiIndex, flag):

        self.sendCommand("SWI" + str(swiIndex) + " FLAG " + str(flag))
        result = self.readResponse()

        return result

    def sendCommandFlagSWI(self, swiIndex):

        self.sendCommand("SWI" + str(swiIndex) + " FLAG COMMAND")
        result = self.readResponse()

        return result

    def sendTransmitFlagSWI(self, swiIndex):

        self.sendCommand("SWI" + str(swiIndex) + " FLAG TRANSMIT")
        result = self.readResponse()

        return result

    def sendIdleFlagSWI(self, swiIndex):

        self.sendCommand("SWI" + str(swiIndex) + " FLAG IDLE")
        result = self.readResponse()

        return result

    def sendSleepFlagSWI(self, swiIndex):

        self.sendCommand("SWI" + str(swiIndex) + " FLAG SLEEP")
        result = self.readResponse()

        return result

    def transmitByteSWI(self, swiIndex, data):

        self.sendCommand("SWI" + str(swiIndex) + " TX " + str(data))
        result = self.readResponse()

        return result

    def receiveBytesSWI(self, swiIndex, count):

        self.sendCommand("SWI" + str(swiIndex) + " RX " + str(count))
        result = self.readResponse()

        return result

    def setPacketOpCodeSWI(self, swiIndex, opCode):

        self.sendCommand("SWI" + str(swiIndex) + " PACKET OPCODE " + str(opCode))
        result = self.readResponse()

        return result

    def setPacketParam1SWI(self, swiIndex, value):

        self.sendCommand("SWI" + str(swiIndex) + " PACKET PARAM1 " + str(value))
        result = self.readResponse()

        return result

    def setPacketParam2SWI(self, swiIndex, value):

        self.sendCommand("SWI" + str(swiIndex) + " PACKET PARAM2 " + str(value))
        result = self.readResponse()

        return result

    def setPacketDataSWI(self, swiIndex, index, value):

        self.sendCommand("SWI" + str(swiIndex) + " PACKET DATA " + str(index) + " " + str(value))
        result = self.readResponse()

        return result

    def setPacketDataFromBufferSWI(self, swiIndex, byteCount, bufferName):

        self.sendCommand("SWI" + str(swiIndex) + " PACKET DATA " + str(byteCount) + " " + str(bufferName))
        result = self.readResponse()

        return result

    def sendPacketSWI(self, swiIndex):

        self.sendCommand("SWI" + str(swiIndex) + " PACKET SEND")
        result = self.readResponse()

        return result

    def clearPacketSWI(self, swiIndex):

        self.sendCommand("SWI" + str(swiIndex) + " PACKET CLEAR")
        result = self.readResponse()

        return result


def _to_hex_string(byte_array):
    """Convert a byte array to a hex string."""

    hex_generator = ("{:02x}".format(x) for x in byte_array)
    return "".join(hex_generator)
