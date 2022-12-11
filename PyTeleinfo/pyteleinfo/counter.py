import logging
import serial
from .serial_management import PortManager
from .serial_management import TeleinfoSerialParameters
from .errors import AbortError


class FrameReader:
    def __init__(self, serialPort, startTag, endTag, bufferSize):
        self.serialPort = serialPort
        self.startTag = startTag
        self.endTag = endTag

        self.loopNumber = 5
        self.bufferSize = bufferSize

    def readFrame(self):
        if self.serialPort is None:
            logging.error("Can't read frame: serial port is None.")
            return ""

        frame = ""
        started = False
        nbRead = 0
        done = False
        for retry in range(self.loopNumber):
            logging.debug("readFrame loop %d" % retry)
            if done:
                break

            for char in self.serialPort.read(self.bufferSize):
                nbRead += 1

                if started and char == self.endTag:
                    logging.debug("End of frame")
                    started = False
                    done = True
                    break

                if char == self.startTag:
                    logging.debug("Start of frame")
                    started = True
                    continue

                if started:
                    frame += chr(char)

        logging.debug("readFrame: total read size = %d" % nbRead)

        if not done:
            logging.debug("Frame not found")
            frame = ""

        return frame


class Counter:
    def __init__(self, config):
        self.dataLines = None

        self.name = config.name
        self.identifier = config.getint("identifier")
        # GPIO used to control counter position
        self.gpioChannel = config.getint("gpioChannel")

        # Serial port parameters
        self.serialParameters = TeleinfoSerialParameters(config)

    @property
    def key(self):
        if self.dataLines is not None:
            tag = self.serialParameters.mapping["key"]
            if tag in self.dataLines:
                return self.dataLines[tag].data

        return None

    def get_data_value(self, mapkey):
        if self.dataLines is not None and mapkey in self.serialParameters.mapping:
            tag = self.serialParameters.mapping[mapkey]
            if tag in self.dataLines:
                return self.dataLines[tag].data

        return None

    def readTeleinfo(self):
        dataLines = None
        try:
            portManager = PortManager(self.gpioChannel, self.identifier)

            # Setup GPIO
            portManager.setupGPIO()

            # Setup serial port
            portManager.setupSerialPort(self.serialParameters)

            retry = 3
            while retry > 0:
                try:
                    # Clean input buffer:
                    portManager.resetBuffer()

                    # Read frame
                    frame = FrameReader(portManager.serialPort,
                                        self.serialParameters.frameParser.startTag,
                                        self.serialParameters.frameParser.endTag,
                                        self.serialParameters.bufferSize).readFrame()

                    # Parse frame
                    dataLines = self.serialParameters.frameParser.parse(frame)

                    # Retry if datalines are empty
                    if len(dataLines) > 0:
                        retry = 0
                    else:
                        logging.debug("No datalines. Will retry (%d)" % retry)
                        dataLines = None
                        retry -= 1
                except ValueError as e:
                    logging.debug("Wrong frame: %s. Will retry (%d)" % (e, retry))
                    dataLines = None
                    retry -= 1

        except KeyboardInterrupt:
            logging.info("Interrupted")
            raise AbortError("Interrupted")
        except serial.serialutil.SerialException as e:
            logging.info("SerialException: %s" % e)
        except Exception:
            logging.exception("Unexpected exception")
        finally:
            portManager.cleanupSerialPort()
            portManager.cleanupGPIO()

        self.dataLines = dataLines
        return dataLines
