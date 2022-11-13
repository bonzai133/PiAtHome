#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
'''
Module to read Teleinfo information for historic and Linky counters (EDF France counters)

Select counter with GPIO, read serial port and write json file with information

@author: l.petit

-------------

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

- Module pyserial : sudo apt-get install python3-serial (import serial)


En bash pour test:
stty -F /dev/ttyAMA0 1200 raw evenp parenb cs7 -crtscts
echo "4" > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio4/direction
echo "0" > /sys/class/gpio/gpio4/value

cat /dev/ttyAMA0

'''

# Disable _created metrics
import os
import argparse
import time
import sys
import configparser
import logging
# import exporter
from pyteleinfo.exporter import register
from pyteleinfo.errors import AbortError
from pyteleinfo.data_writer import DataWriter
from pyteleinfo.counter import Counter


def process(args):
    """
    Main loop process
    """

    # Create logger with basic config
    if args.logFile is not None:
        logging.basicConfig(filename=args.logFile, format='%(asctime)s: [%(levelname)s] %(message)s', level=args.logLevel)

    if args.debug:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=args.logLevel)
        logging.info("-- Debug mode activated --")

    logging.warning("Started with args: %s" % repr(args))

    # Load configuration
    if args.configFile is not None:
        configFile = args.configFile
    else:
        configFile = os.path.splitext(__file__)[0] + ".conf"

    config = configparser.ConfigParser()
    config.read(configFile)

    # Datawriter
    dataWriter = None
    if args.writeToFile != "":
        dataWriter = DataWriter(args.writeToFile)

    # Add counters in the list to check
    countersToCheck = []
    if args.consumption:
        countersToCheck.append(Counter(config['Consumption']))

    if args.production:
        countersToCheck.append(Counter(config['Production']))

    if args.fake:
        countersToCheck.append(Counter(config['Fake']))

    # Register Prometheus metrics
    teleinfoMetrics = register(args, config['Metrics'])

    # Check if we run as a service
    loop = True
    while loop:
        if not args.service:
            loop = False

        if len(countersToCheck) < 1:
            logging.error("Must specify at least one counter")
            break

        try:
            for counter in countersToCheck:
                logging.info("-- Start %s" % (counter.name))
                info = counter.readTeleinfo()
                logging.info("%s Teleinfo: %s" % (counter.name, info))

                # Update Prometheus
                teleinfoMetrics.update(counter)

                # Write data
                if dataWriter is not None and info is not None:
                    logging.debug("Write data")
                    try:
                        dataWriter.write(info)
                    except KeyError:
                        logging.error("Key not found in teleinfo: %s" % info)

                # Wait a while in service mode
                if args.service:
                    logging.debug("Sleep")
                    time.sleep(args.sleepTime)
        except AbortError as e:
            logging.info(e)
            sys.exit(0)
        except KeyboardInterrupt:
            logging.info("Interrupted (2)")
            sys.exit(0)

    logging.warning("-- End of process --")


def main():
    '''
    Main entry point

    :return:
    '''

    # Get parameters
    parser = argparse.ArgumentParser(description='Read values from teleinfo interface')

    parser.add_argument('-i', '--config-file', dest='configFile', action='store', help='Config file path')

    parser.add_argument('-c', '--consumption-counter', dest='consumption', action='store_true',
                        help='Get info from consumption counter')
    parser.add_argument('-p', '--production-counter', dest='production', action='store_true',
                        help='Get info from production counter')
    parser.add_argument('-f', '--fake-counter', dest='fake', action='store_true', help='Get info from fake counter')
    parser.add_argument('-s', '--service', action='store_true', help='Start as a service (infinite loop)')

    parser.add_argument('-d', '--dbname', dest='dbFileName', action='store', help='Database filename', default='')
    parser.add_argument('-w', '--write-to-file', dest='writeToFile', action='store',
                        help='Path and prefix of file to write. Counter label will be append.\
                              Use /var/run/shm/teleinfo for example.',
                        default='')
    parser.add_argument('-m', '--sleep-time', dest='sleepTime', type=float, action='store',
                        help='Sleep time between each read in service mode', default=15)

    parser.add_argument('-l', '--log-file', dest='logFile', action='store', help='Log file path')
    parser.add_argument('-e', '--log-level', dest='logLevel', action='store',
                        help='Log level DEBUG, INFO, WARNING, ERROR', default='INFO')

    parser.add_argument('-g', '--debug', dest='debug', action='store_true', help='Display log on console')

    parser.add_argument('-o', '--metrics-port', dest='metrics_port', type=int, action='store',
                        help='Enable Prometheus metrics', default=0)

    args = parser.parse_args()

    # Start main process loop
    process(args)


if __name__ == "__main__":
    main()
