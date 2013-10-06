#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import traceback
import RPi.GPIO as GPIO
import serial
import re

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


def setupSerial():
    try:
        serial_port = serial.Serial(SERIAL_PORT_NAME, baudrate=SERIAL_PORT_BAUDRATE,
                                    bytesize=SERIAL_PORT_DATABITS,
                                    parity=SERIAL_PORT_PARITY, stopbits=SERIAL_PORT_STOPBITS,
                                    rtscts=SERIAL_PORT_RTSCTS, timeout=SERIAL_PORT_READTIMEOUT)
    except Exception, e:
        print "Exception in setupSerial: %s" % e
    
    wainting_chars = serial_port.inWaiting()
    if wainting_chars != 0:
        print "Warning : there is some chars in the buffer. We are not alone !"
    
    return serial_port


def cleanupSerial(serPort):
    serPort.close()


#===============================================================================
# Read and parse
#===============================================================================
def readFrame(serPort):
    #Discard first byte (can be erroneous)
    serPort.read(25)

    frame = ""
    rcv = ""
    while frame == "":
        rcv += serPort.read(100)
        #print str(rcv)
        if len(rcv) == 0:
            print "No data received"
        else:
            print '%d bytes received' % len(rcv)
            
            #print repr(rcv)

            frames_grp = str(rcv).split(chr(0x02))
            if len(frames_grp) < 3:
                print "Not enought data received"
            else:
                print "Groups: %d" % len(frames_grp)
                print repr(frames_grp)
                
                #Skip first and last group (incomplete)
                for index in range(1, len(frames_grp) - 1):
                    frm_grp = frames_grp[index]
                    if frm_grp[-1:] == chr(0x03):
                        #ret_frames.append(frm_grp.rstrip(chr(0x03)))
                        frame = frm_grp.rstrip(chr(0x03))
                        break
                    else:
                        print "No end tag in frame (%d) : %s" % (index, frm_grp)
           
    return frame


def parseFrame(frame):
    #print repr(frame)
    messages = frame.replace('\n', '').split('\r')

    data = {}
    for msg in messages:
        try:
            (code, val, ctrl) = msg.split()
            #print "%s: %s" % (code, val)

            data[code] = val
        except Exception, e:
            if msg != "":
                print "Can't split: %s" % msg

    return data

#===============================================================================
# Data export
#===============================================================================
def exportData(data):
    print data


#===============================================================================
# Read teleinfo main function
#===============================================================================
def readTeleinfo(counterPos):
    try:
        setupGPIO(counterPos)

        serPort = setupSerial()
        
        frame = readFrame(serPort)
        
        data = parseFrame(frame)
        
        exportData(data)
        
    except Exception, e:
        print "Unexpected exception: %s" % e
        traceback.print_exc()
    finally:
        cleanupSerial(serPort)
        cleanupGPIO()


#===============================================================================
# main
#===============================================================================
def main():
    print "--- CONSOMMATION ---"
    readTeleinfo(COUNTER_POS_CONSO)
    print
    #print "--- PRODUCTION ---"
    #readTeleinfo(COUNTER_POS_PROD)

if __name__ == "__main__":
        main()
