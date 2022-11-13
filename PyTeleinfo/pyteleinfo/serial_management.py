import logging
import json
import serial
from .counter_id import CounterId
from .parsers import HistoricParser, LinkyParser

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi module not installed: will continue for testing")
except RuntimeError as e:
    print(e)
    print("I hope we are only testing !")


class SerialPortFile:
    '''
    Read data in a file instead of real serial port
    '''

    def __init__(self, filename):
        self.filename = filename

        self.fp = open(filename, 'rb')

    def close(self):
        self.fp.close()

    def read(self, size):
        return self.fp.read(size)


class PortManager:
    def __init__(self, gpioChannel, counterPosition, debug=False):
        self.gpioChannel = gpioChannel

        self.serialPort = None
        self.counterPosition = counterPosition

        self.debug = debug

    def resetBuffer(self):
        """
        Discard existing data in input buffer
        :return:
        """
        logging.debug("resetBuffer")
        if self.serialPort is not None:
            if hasattr(self.serialPort, 'reset_input_buffer'):
                self.serialPort.reset_input_buffer()
            elif hasattr(self.serialPort, 'flushInput'):
                self.serialPort.flushInput()

    def setupGPIO(self):
        logging.debug("setupGPIO")
        if self.counterPosition != CounterId.FAKE_ID:
            # Disable GPIO warnings except in debug mode
            if not self.debug:
                GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BOARD)

            gpioValues = {CounterId.CONSUMPTION_ID: GPIO.LOW, CounterId.PRODUCTION_ID: GPIO.HIGH}

            gpioValue = gpioValues[self.counterPosition]
            GPIO.setup(self.gpioChannel, GPIO.OUT, initial=gpioValue)

    def cleanupGPIO(self):
        logging.debug("cleanupGPIO")
        if self.counterPosition != CounterId.FAKE_ID:
            GPIO.cleanup()

    def setupSerialPort(self, serialPortParameters):
        logging.debug("setupSerialPort")
        self.serialPort = None

        if serialPortParameters.serialPortFileName != "":
            # Data is in a file (for testing)
            self.serialPort = SerialPortFile(serialPortParameters.serialPortFileName)
        else:
            # Real serial port
            try:
                self.serialPort = serial.Serial(serialPortParameters.serialPortName,
                                                baudrate=serialPortParameters.serialPortBaudRate,
                                                bytesize=serialPortParameters.serialPortDatabits,
                                                parity=serialPortParameters.serialPortParity,
                                                stopbits=serialPortParameters.serialPortStopBits,
                                                rtscts=serialPortParameters.serialPortRtsCts,
                                                timeout=serialPortParameters.serialPortReadTimeout)

                # Check if some chars are in the buffer
                if self.serialPort.inWaiting() != 0:
                    logging.warning("There is some chars in the buffer. We are not alone !")
            except Exception as e:
                logging.error("Exception in setupSerial: %s" % e)

    def cleanupSerialPort(self):
        logging.debug("cleanupSerialPort")
        if self.serialPort:
            self.serialPort.close()


class TeleinfoSerialParameters():
    def __init__(self, config) -> None:
        # For fake serial port
        self.serialPortFileName = config["serialPortFileName"]

        # Buffer size
        self.bufferSize = config.getint("bufferSize")

        # Serial port name
        self.serialPortName = config["serialPortName"]
        self.serialPortReadTimeout = config.getfloat("serialPortReadTimeout")

        self.serialPortBaudRate = config.getint("serialPortBaudRate")
        self.serialPortDatabits = config.getint("serialPortDatabits")
        self.serialPortParity = config["serialPortParity"]
        self.serialPortStopBits = config.getint("serialPortStopBits")
        self.serialPortRtsCts = config.getboolean("serialPortRtsCts")

        # Frame parser
        if config["teleinfo_type"] == "Historic":
            self.frameParser = HistoricParser()
        elif config["teleinfo_type"] == "Linky":
            self.frameParser = LinkyParser()
        else:
            self.frameParser = LinkyParser()

        # Key mapping
        self.mapping = json.loads(config["metrics_mapping"])
