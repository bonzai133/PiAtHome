#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Module to read Teleinfo information for historic and Linky counters (EDF France counters)

Select counter with GPIO, read serial port and write json file with information

@author: l.petit
'''

'''
Récupération des données de teleinfo edf sur le compteur de production et de consommation

Branchement de la carte: entre [] c'est les GPIO du BCM2835
(1)  3v3
(6)  GND
(7)  GPIO 7 [GPIO 4]: choix du compteur
(10) UART RXD [GPIO 15]: réception des données séries

Configuration des GPIO:
- Bibliothèque RPi.GPIO (import RPi.GPIO as GPIO) : version actuelle 0.5.3a
- GPIO.setmode(GPIO.BOARD / GPIO.BCM)
- GPIO.setup(channel, GPIO.OUT, initial=GPIO.HIGH)
- GPIO.input(channel)
- GPIO.output(channel, state)
- GPIO.cleanup()

Port Série:
- Libérer le port (initalement utilisé par le kernel): https://github.com/lurch/rpi-serial-cons
  Modif des fichiers :
   # /boot/cmdline.txt
   # /etc/inittab

- Module pyserial : sudo apt-get install python-serial (import serial)


En bash pour test:
stty -F /dev/ttyAMA0 1200 sane evenp parenb cs7 -crtscts
echo "4" > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio4/direction
echo "0" > /sys/class/gpio/gpio4/value

cat /dev/ttyAMA0

'''

import argparse
import serial
import time
from json import JSONEncoder
import json
import logging

try:
    import RPi.GPIO as GPIO
except ImportError as e:
    print("RPi module not installed: will continue for testing")


class DataLineEncoder(JSONEncoder):
    def default(self, object):
        if isinstance(object, DataLine):
            return object.toJson()
        else:
            # call base class implementation which takes care of
            # raising exceptions for unsupported types
            return json.JSONEncoder.default(self, object)


class DataLine:
    def __init__(self, line, separator, addSeparatorInChecksum):
        self.line = line
        self.separator = separator
        self.addSeparatorInChecksum = addSeparatorInChecksum

        self.tag = ""
        self.horodate = ""
        self.data = ""
        self.checksumValue = ""

        self._parse(line)

    def __str__(self):
        return self.toJson()

    def __repr__(self):
        return "%s: %s|%s|%s" % (self.tag, self.horodate, self.data, self.checksumValue)

    def toJson(self):
        if self.horodate != "":
            return self.horodate + '|' + self.data

        return self.data

    def _parse(self, line):
        group = line.split(chr(self.separator))

        if len(group) == 3:
            (tag, data, checksum) = group
            horodate = ""
        elif len(group) == 4:
            (tag, horodate, data, checksum) = group
        else:
            raise ValueError("Wrong line format: %s" % group)

        checksum = ord(checksum)
        if not self.verifyChecksum(tag, horodate, data, checksum):
            raise ValueError("Wrong cheksum: %s" % group)

        self.tag = tag
        self.horodate = horodate
        self.data = data
        self.checksumValue = checksum

    def verifyChecksum(self, tag, horodate, data, checksum):
        calculatedChecksum = self.checkSum(tag, horodate, data)

        if calculatedChecksum == checksum:
            return True

        return False

    def checkSum(self, tag, horodate, data):
        # TODO: Move checksum to Frame Parsers
        '''
         Le principe de calcul de la Checksum est le suivant :
         - calcul de la somme « S1 » de tous les caractères allant du début du champ « Etiquette » jusqu’au délimiteur (inclus) entre les
         champs « Donnée » et « Checksum ») ;
         - cette somme déduite est tronquée sur 6 bits (cette opération est faite à l’aide d’un ET logique avec 0x3F) ;
         - pour obtenir le résultat checksum, on additionne le résultat précédent S2 à 0x20.
         En résumé :
         Checksum = (S1 & 0x3F) + 0x20
         Le résultat sera toujours un caractère ASCII imprimable compris entre 0x20 et 0x5F.

         :return:
         '''
        checksum = 0

        sep = chr(self.separator)
        if horodate == "":
            line = tag + sep + data
        else:
            line = tag + sep + horodate + sep + data

        for c in line:
            checksum += ord(c)

        if self.addSeparatorInChecksum:
            checksum += self.separator

        checksum = (checksum & 0x3F) + 0x20
        return checksum


class FrameParser:
    def __init__(self):
        pass

    def parse(self, frame):
        if frame == "":
            return {}

        dataLines = {}
        for line in frame.split('\n'):
            if line:
                d = DataLine(line.strip('\r'), self.separator, self.addSeparatorInChecksum)
                dataLines[d.tag] = d

        return dataLines


class HistoricParser(FrameParser):
    '''
    Parse historic teleinfo frame
    <LF> (0x0A) | Etiquette | <SP> (0x20) | Donnée | <SP> (0x20) | Checksum | <CR> (0x0D)
                | Zone contrôlée par le checksum   |
    '''
    startTag = 0x02
    endTag = 0x03
    separator = 0x20
    addSeparatorInChecksum = False


class LinkyParser(FrameParser):
    '''
    Parse linky (TIC v2) teleinfo frame
    STX (0x02) | Data Set | Date Set  | ... | Data Set | ETX (0x03)

    Dataset with Horodate:
    <LF> (0x0A) | Etiquette | <HT> (0x09) | Horodate | <HT> (0x09) | Donnée | <HT> (0x09) | Checksum | <CR> (0x0D)
                | Zone contrôlée par le checksum                            |

    Dataset without Horodate:
    <LF> (0x0A) | Etiquette | <HT> (0x09) | Donnée | <HT> (0x09) | Checksum | <CR> (0x0D)
                | Zone contrôlée par le checksum   |
    '''
    startTag = 0x02
    endTag = 0x03
    separator = 0x09
    addSeparatorInChecksum = True


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


class FakeTeleinfoSerialParameters:
    # For fake serial port
    serialPortFileName = "tic_std1.txt"

    # Frame parser
    frameParser = LinkyParser()


class HistoricTeleinfoSerialParameters:
    # For fake serial port
    serialPortFileName = ""

    # Serial port name
    serialPortName = "/dev/serial0"
    serialPortReadTimeout = 3.0

    serialPortBaudRate = 1200
    serialPortDatabits = serial.SEVENBITS
    serialPortParity = serial.PARITY_EVEN
    serialPortStopBits = serial.STOPBITS_ONE
    serialPortRtsCts = True

    # Frame parser
    frameParser = HistoricParser()


class LinkyTeleinfoSerialParameters:
    # For fake serial port
    serialPortFileName = ""

    # Serial port name
    serialPortName = "/dev/serial0"
    serialPortReadTimeout = 3.0

    serialPortBaudRate = 9600
    serialPortDatabits = serial.SEVENBITS
    serialPortParity = serial.PARITY_EVEN
    serialPortStopBits = serial.STOPBITS_ONE
    serialPortRtsCts = True

    # Frame parser
    frameParser = LinkyParser()


class PortManager:
    def __init__(self, gpioChannel, counterPosition):
        self.gpioChannel = gpioChannel

        self.serialPort = None
        self.counterPosition = counterPosition

    def setupGPIO(self):
        if self.counterPosition != Counter.FAKE_ID:
            GPIO.setmode(GPIO.BOARD)

            gpioValues = {Counter.CONSUMPTION_ID: GPIO.LOW, Counter.PRODUCTION_ID: GPIO.HIGH}

            gpioValue = gpioValues[self.counterPosition]
            GPIO.setup(self.gpioChannel, GPIO.OUT, initial=gpioValue)

    def cleanupGPIO(self):
        if self.counterPosition != Counter.FAKE_ID:
            GPIO.cleanup()

    def setupSerialPort(self, serialPortParameters):
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
        if self.serialPort:
            self.serialPort.close()


class FrameReader:
    def __init__(self, serialPort, startTag, endTag):
        self.serialPort = serialPort
        self.startTag = startTag
        self.endTag = endTag

        self.loopNumber = 10
        self.bufferSize = 255


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
                    started = False
                    done = True
                    break

                if char == self.startTag:
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
    FAKE_ID = -1
    PRODUCTION_ID = 0
    CONSUMPTION_ID = 1

    def __init__(self, identifier, serialParameters, gpioChannel):
        self.identifier = identifier
        self.serialParameters = serialParameters

        # GPIO used to control counter position
        self.gpioChannel = gpioChannel

    def readTeleinfo(self):
        serialPort = None
        dataLines = None
        try:
            portManager = PortManager(self.gpioChannel, self.identifier)

            # Setup GPIO
            portManager.setupGPIO()

            # Setup serial port
            serialPort = portManager.setupSerialPort(self.serialParameters)

            # Read frame
            frame = FrameReader(portManager.serialPort,
                                self.serialParameters.frameParser.startTag,
                                self.serialParameters.frameParser.endTag).readFrame()

            # Parse frame
            dataLines = self.serialParameters.frameParser.parse(frame)

        except Exception:
            logging.exception("Unexpected exception")
        finally:
            portManager.cleanupSerialPort()
            portManager.cleanupGPIO()

        return dataLines


class ProductionCounter(Counter):
    def __init__(self):
        super(ProductionCounter, self).__init__(0, LinkyTeleinfoSerialParameters, 7)


class ConsumptionCounter(Counter):
    def __init__(self):
        super(ConsumptionCounter, self).__init__(1, HistoricTeleinfoSerialParameters, 7)


class FakeCounter(Counter):
    def __init__(self):
        super(FakeCounter, self).__init__(-1, FakeTeleinfoSerialParameters, 7)


class DataWriter:
    def __init__(self, filenamePrefix):
        self.filenamePrefix = filenamePrefix

    def write(self, dataLines):
        filename = ''
        if 'ADCO' in dataLines.keys():
            filename = self.filenamePrefix + dataLines['ADCO'].data
        elif 'ADSC' in dataLines.keys():
            filename = self.filenamePrefix + dataLines['ADSC'].data
        else:
            logging.debug("ADCO or ADSC not found in data: %s" % dataLines.keys())
            raise KeyError("Can't find counter key in data")

        logging.debug("Will write to file %s" % filename)
        with open(filename, 'w') as fp:
            json.dump(dataLines, fp, cls=DataLineEncoder)


def main():
    '''
    Main entry point

    :return:
    '''

    # Get parameters
    parser = argparse.ArgumentParser(description='Read values from teleinfo interface')

    parser.add_argument('-c', '--consumption-counter', dest='consumption', action='store_true', help='Get info from consumption counter')
    parser.add_argument('-p', '--production-counter', dest='production', action='store_true', help='Get info from production counter')
    parser.add_argument('-f', '--fake-counter', dest='fake', action='store_true', help='Get info from fake counter')
    parser.add_argument('-s', '--service', action='store_true', help='Start as a service (infinite loop)')

    parser.add_argument('-d', '--dbname', dest='dbFileName', action='store', help='Database filename', default='')
    parser.add_argument('-w', '--write-to-file', dest='writeToFile', action='store',
                        help='Path and prefix of file to write. Counter label will be append. Use /var/run/shm/teleinfo for example.',
                        default='')
    parser.add_argument('-m', '--sleep-time', dest='sleepTime', action='store', help='Sleep time between each read in service mode', default=15)

    parser.add_argument('-l', '--log-file', dest='logFile', action='store', help='Log file path')
    parser.add_argument('-e', '--log-level', dest='logLevel', action='store', help='Log level DEBUG, INFO, WARNING, ERROR', default='INFO')

    parser.add_argument('-g', '--debug', dest='debug', action='store_true', help='Display log on console')

    args = parser.parse_args()

    # Create logger with basic config
    if args.logFile is not None:
        logging.basicConfig(filename=args.logFile, format='%(levelname)s:%(message)s', level=args.logLevel)

    if args.debug:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=args.logLevel)
        logging.info("-- Debug mode activated --")

    logging.debug("Args: %s" % repr(args))

    # Datawriter
    dataWriter = None
    if args.writeToFile != "":
        dataWriter = DataWriter(args.writeToFile)

    # Check if we run as a service
    loop = True
    while loop:
        if not args.service:
            loop = False

        if not args.consumption and not args.production and not args.fake:
            logging.error("Must specify at least one counter")
            break

        if args.consumption:
            info = ConsumptionCounter().readTeleinfo()
            logging.info("Consumption Teleinfo: %s" % info)
            if dataWriter:
                dataWriter.write(info)

            if args.service:
                time.sleep(args.sleepTime)

        if args.production:
            info = ProductionCounter().readTeleinfo()
            logging.info("Production Teleinfo: %s" % info)
            if dataWriter:
                dataWriter.write(info)

            if args.service:
                time.sleep(args.sleepTime)

        if args.fake:
            info = FakeCounter().readTeleinfo()
            logging.info("Fake Teleinfo: %s" % info)
            if dataWriter:
                dataWriter.write(info)

            if args.service:
                time.sleep(args.sleepTime)

    logging.debug("-- End of process --")


if __name__ == "__main__":
    main()