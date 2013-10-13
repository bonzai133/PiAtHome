#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Created on 26 sept. 2013

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

import serial
port = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=3.0)
while True:
    port.write("\r\nSay something:")
    rcv = port.read(10)
    port.write("\r\nYou sent:" + repr(rcv))

disponibilité du port, utiliser port.inWaiting() == 0

Config du port série (à faire en Python):
sudo stty -F /dev/ttyAMA0 1200 sane evenp parenb cs7 -crtscts
1200 bits/s, 7 bits/caractères, parité paire, 1 bit de stop.

- Décodage de la trame (http://vesta.homelinux.free.fr/site/wiki/demodulateur_teleinformation_edf.html)

Groupe de trame:
STX (code ASCII = 02), et se termine par ETX (03).

Début : 0x0A
Fin   : 0x0D

LF (0x0A) Etiquette (4 à 8 caractères) SP (0x20) Données (1 à 12 caractères) SP (0x20) CC (caractère de contrôle) CR (0x0D)
    n° d'identification du compteur, étiquette: ADCO (12 caractères)
    option tarifaire (type d'abonnement) : OPTARIF (4 car.)
    intensité souscrite : ISOUSC ( 2 car. unité = ampères)
    index si option = base : BASE ( 9 car. unité = Wh)
    index heures creuses si option = heures creuses : HCHC ( 9 car. unité = Wh)
    index heures pleines si option = heures creuses : HCHP ( 9 car. unité = Wh)
    index heures normales si option = EJP : EJP HN ( 9 car. unité = Wh)
    index heures de pointe mobile si option = EJP : EJP HPM ( 9 car. unité = Wh)
    index heures creuses jours bleus si option = tempo : BBR HC JB ( 9 car. unité = Wh)
    index heures pleines jours bleus si option = tempo : BBR HP JB ( 9 car. unité = Wh)
    index heures creuses jours blancs si option = tempo : BBR HC JW ( 9 car. unité = Wh)
    index heures pleines jours blancs si option = tempo : BBR HP JW ( 9 car. unité = Wh)
    index heures creuses jours rouges si option = tempo : BBR HC JR ( 9 car. unité = Wh)
    index heures pleines jours rouges si option = tempo : BBR HP JR ( 9 car. unité = Wh)
    préavis EJP si option = EJP : PEJP ( 2 car.) 30mn avant période EJP
    période tarifaire en cours : PTEC ( 4 car.)
    couleur du lendemain si option = tempo : DEMAIN
    intensité instantanée : IINST ( 3 car. unité = ampères)
    avertissement de dépassement de puissance souscrite : ADPS ( 3 car. unité = ampères) (message émis uniquement en cas de dépassement effectif, dans ce cas il est immédiat)
    intensité maximale : IMAX ( 3 car. unité = ampères)
    Puissance apparente : PAPP ( 5 car. unité = Volt.ampères)
    groupe horaire si option = heures creuses ou tempo : HHPHC (1 car.)
    mot d'état (autocontrôle) : MOTDETAT (6 car.)

En bash pour test:
stty -F /dev/ttyAMA0 1200 sane evenp parenb cs7 -crtscts
echo "4" > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio4/direction
echo "0" > /sys/class/gpio/gpio4/value

cat /dev/ttyAMA0

==== CONSO

ADCO 030928249097 L

OPTARIF BASE 0

ISOUSC 30 9

BASE 008327404 '

PTEC TH.. $

IINST 001 X

IMAX 032 D

PAPP 00300 $



===== PROD

ADCO 030928248994 Q

OPTARIF BASE 0

ISOUSC 15 <

BASE 012569585 4

PTEC TH.. $

IINST 000 W

IMAX 012 B

PAPP 00070 (




'''
import os
import re
import logging
import logging.config
import argparse
import sqlite3
from datetime import datetime

try:
    import RPi.GPIO as GPIO
except ImportError, e:
    print "RPi module must be installed"
    
    #Fake GPIO class for unit tests
    class cGPIO:
        BOARD = 0
        LOW = 0
        HIGH = 1
        OUT = 0
        
        def setup(self, chanel, direction, initial=0):
            pass
        
        def setmode(self, mode):
            pass
        
        def cleanup(self):
            pass
    GPIO = cGPIO()
    
import serial

#Logger
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
LOGCONF_PATH = os.path.join(ROOT_PATH, 'logging.conf')

logging.config.fileConfig(LOGCONF_PATH)
logger = logging.getLogger(__name__)


#Counter position (teleinfo input)
COUNTER_POS_PROD = 0
COUNTER_POS_CONSO = 1

#GPIO used to control counter position
CHANNEL_GPIO = 7

#Serial port
SERIAL_PORT_NAME = "/dev/ttyAMA0"
SERIAL_PORT_BAUDRATE = 1200
SERIAL_PORT_DATABITS = serial.SEVENBITS
SERIAL_PORT_PARITY = serial.PARITY_EVEN
SERIAL_PORT_STOPBITS = serial.STOPBITS_ONE
SERIAL_PORT_RTSCTS = True
SERIAL_PORT_READTIMEOUT = 3.0


#===============================================================================
# Configuration
#===============================================================================
def setupGPIO(counterPos):
    GPIO.setmode(GPIO.BOARD)
    
    if counterPos == COUNTER_POS_CONSO:
        intial_value = GPIO.LOW
    else:
        intial_value = GPIO.HIGH
        
    GPIO.setup(CHANNEL_GPIO, GPIO.OUT, initial=intial_value)


def cleanupGPIO():
    GPIO.cleanup()


def setupSerial(serialPortName):
    serial_port = None
    try:
        serial_port = serial.Serial(serialPortName, baudrate=SERIAL_PORT_BAUDRATE,
                                    bytesize=SERIAL_PORT_DATABITS,
                                    parity=SERIAL_PORT_PARITY, stopbits=SERIAL_PORT_STOPBITS,
                                    rtscts=SERIAL_PORT_RTSCTS, timeout=SERIAL_PORT_READTIMEOUT)
    
        wainting_chars = serial_port.inWaiting()
        if wainting_chars != 0:
            logger.warning("There is some chars in the buffer. We are not alone !")
    except Exception, e:
        logger.error("Exception in setupSerial: %s" % e)
    
    return serial_port


def cleanupSerial(serPort):
    if serPort:
        serPort.close()


#===============================================================================
# Read and parse
#===============================================================================
def readFrame(serPort):
    if serPort is None:
        return ""
    
    #Discard first byte (can be erroneous)
    serPort.read(25)

    frame = ""
    rcv = ""
    while frame == "":
        rcv += serPort.read(255)
        if len(rcv) == 0:
            logger.warning("No data received")
        else:
            logger.debug('%d bytes received' % len(rcv))
            logger.debug(repr(rcv))

            frames_grp = str(rcv).split(chr(0x02))
            if len(frames_grp) < 3:
                logger.info("Not enought data received")
            else:
                logger.debug("Groups: %d" % len(frames_grp))
                logger.debug(repr(frames_grp))
                
                #Skip first and last group (incomplete)
                for index in range(1, len(frames_grp) - 1):
                    frm_grp = frames_grp[index]
                    if frm_grp[-1:] == chr(0x03):
                        frame = frm_grp.rstrip(chr(0x03))
                        break
                    else:
                        logger.info("No end tag in frame (%d) : %s" % (index, frm_grp))
           
    return frame


def verifyCheksum(code, val, ctrl):
    chk = 0
    for c in "%s %s" % (code, val):
        chk += ord(c)
        
    chk = (chk & 0x3F) + 0x20
    
    logger.debug("verifyCheksum: calculated[%d], received[%d]" % (chk, ord(ctrl)))
    if chk == ord(ctrl):
        return True
    else:
        return False


def parseFrame(frame):
    re_msg = re.compile("(.*) (.*) (.)")
    messages = frame.replace('\n', '').split('\r')
    
    data = {}
    for msg in messages:
        if len(msg) == 0:
            continue
        
        try:
            splitted = re_msg.split(msg)
            
            if splitted and len(splitted) == 5:
                code = splitted[1]
                val = splitted[2]
                ctrl = splitted[3]

                logger.debug("%s: %s" % (code, val))
            
                if not verifyCheksum(code, val, ctrl):
                    logger.warning("Checksum doesn't match for msg: %s" % msg)

                data[code] = val
            else:
                logger.warning("Badly splitted: %s" % msg)
        except Exception, e:
            if msg != "":
                logger.warning("Can't split: %s" % msg)

    return data


#===============================================================================
# Data export
#===============================================================================
def exportData(data, dbFileName):
    if dbFileName == "":
        logger.info("Will print data")
        displayData(data)
    else:
        logger.info("Will store data in %s" % dbFileName)
        writeDataToDb(data, dbFileName)


def displayData(data):
    print data

  
def writeDataToDb(data, dbFileName):
    logger.debug("%s -> %s" % (data, dbFileName))
    
    db = DBManager(dbFileName)
    if db.connectFailure == 1:
        logger.error("Can't connect to database '%s'" % dbFileName)
    else:
        db.CreateTables(Teleinfo_dbTables)
        
        #db Execute query insert data
        try:
            counterId = data['ADCO']
            indexBase = data['BASE']
            iMax = data['IMAX']
            date = datetime.now()
            
            query = 'INSERT INTO TeleinfoDaily (date, counterId, indexBase, iMax) \
                     VALUES ("%s", "%s", "%s", "%s")'
            
            db.ExecuteRequest(query % (date, counterId, indexBase, iMax))
            db.Commit()
            
        except KeyError, e:
            logger.error("Can't store data. Missing key: '%s'" % e)

        db.Close()
        
        
#===========================================================================
# TODO: à supprimer : utiliser module externe
#===========================================================================
Teleinfo_dbTables = {"TeleinfoDaily": [('date', "d", "Date"),
                        ('counterId', "n", "Counter identifier (serial number)"),
                        ('indexBase', "n", "Base index (Wh)"),
                        ('iMax', "n", "Maximal intensity")], }


class DBManager:
    """Management of a MySQL database"""
    
    def __init__(self, dbFileName):
        "Connect and create the cursor"
        try:
            self.connection = sqlite3.connect(dbFileName)
        except Exception, err:
            logging.error("DB Connect failed: %s" % err)
            self.connectFailure = 1
        else:
            self.cursor = self.connection.cursor()
            self.connectFailure = 0
    
    def CreateTables(self, dictTables):
        for table in dictTables.keys():
            req = "CREATE TABLE IF NOT EXISTS %s (" % table
            
            for descr in dictTables[table]:
                fieldName = descr[0]
                fType = descr[1]
                
                if fType == 'n':
                    fieldType = 'INTEGER'
                elif fType == 'r':
                    fieldType = 'REAL'
                elif fType == 'd':
                    fieldType = 'TEXT PRIMARY KEY'
                elif fType == 't':
                    fieldType = 'TEXT'
                else:
                    fieldType = 'BLOB'
                    
                req = req + "%s %s, " % (fieldName, fieldType)
                
            req = req[:-2] + ")"
                
            self.ExecuteRequest(req)
                
    def DeleteTables(self, dictTables):
        for table in dictTables.keys():
            req = "DROP TABLE %s" % table
            self.ExecuteRequest(req)
        self.Commit()
    
    def ExecuteRequest(self, req):
        logger.debug("Request: %s" % req)
        try:
            self.cursor.execute(req)
        except Exception, err:
            logging.error("Incorrect SQL request (%s)\n%s" % (req, err))
            return 0
        else:
            return 1
    
    def GetResult(self):
        return self.cursor.fetchall()
        
    def Commit(self):
        if self.connection:
            self.connection.commit()
                    
    def Close(self):
        if self.connection:
            self.connection.close()


#===============================================================================
# Read teleinfo main function
#===============================================================================
def readTeleinfo(serialPortName, interface, dbFileName):
    serPort = None
    try:
        #Setup of ports
        setupGPIO(interface)
        serPort = setupSerial(serialPortName)
        
        #Read frame
        frame = readFrame(serPort)
        data = parseFrame(frame)
        
        #Write data
        exportData(data, dbFileName)
        
    except Exception:
        logger.exception("Unexpected exception")
    finally:
        cleanupSerial(serPort)
        cleanupGPIO()


#===============================================================================
# main
#===============================================================================
def main():
    #Get parameters
    parser = argparse.ArgumentParser(description='Read values from teleinfo interface')
    
    parser.add_argument('-p', '--portName', dest='serialPortName', action='store',
                        help='Serial port name', default=SERIAL_PORT_NAME)
    parser.add_argument('-i', '--interface', dest='interface', type=int, action='store',
                        help='Teleinfo interface : 0 for Production, 1 for Consumption', default=COUNTER_POS_CONSO)
    parser.add_argument('-d', '--dbname', dest='dbFileName', action='store',
                        help='Database filename', default='')

    args = parser.parse_args()

    logger.info("Args: %s" % repr(args))
    
    #Check arguments
    if args.interface < 0 or args.interface > 1:
        logger.error("Interface must be 0 or 1")
        parser.error("Interface must be 0 or 1")
    
    readTeleinfo(args.serialPortName, args.interface, args.dbFileName)
    
    logger.info("----- End of treatment")


if __name__ == "__main__":
    main()
