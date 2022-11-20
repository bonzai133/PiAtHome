import logging
import json
import argparse
import configparser
import time
from pysolarmax.Inverter import Inverter

import os
os.environ['PROMETHEUS_DISABLE_CREATED_SERIES'] = "True"

from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily
from prometheus_client import REGISTRY, GC_COLLECTOR, PLATFORM_COLLECTOR

REGISTRY.unregister(GC_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
# REGISTRY.unregister(PROCESS_COLLECTOR)


class SolarmaxCollector(object):
    def __init__(self, config) -> None:
        self.metrics = json.loads(config['metrics'])
        self.address = config['address']
        self.port = config.getint('port')

    def collect(self):
        # Read values
        values = self.read_values()

        # Update metrics

        for key, cmd_obj in values.items():
            prop = self.metrics[key]
            yield GaugeMetricFamily(prop[0], prop[1], value=cmd_obj.Value)

    def read_values(self):
        # Connect to inverter
        inverter = Inverter(self.address, self.port)

        if not inverter.connect():
            logging.debug("Can't connect to inverter")
            return {}

        values = inverter.getValues(list(self.metrics.keys()))

        inverter.disconnect()

        return values


def register(args, config):
    # Start Prometheus serveur and register gauges in service mode only
    logging.info("Starting Prometheus exporter")
    start_http_server(args.metrics_port)

    # Create metrics
    REGISTRY.register(SolarmaxCollector(config))


def process(args):
    '''
    Main loop process
    '''
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

    # Register Prometheus metrics
    register(args, config['DEFAULT'])

    # Check if we run as a service
    while True:
        time.sleep(10000)


def main():
    '''
    Main entry point

    :return:
    '''

    # Get parameters
    parser = argparse.ArgumentParser(description='Read values from Solarmax inverter')

    parser.add_argument('-i', '--config-file', dest='configFile', action='store', help='Config file path')

    parser.add_argument('-o', '--metrics-port', dest='metrics_port', type=int, action='store',
                        help='Enable Prometheus metrics', default=8000)

    parser.add_argument('-l', '--log-file', dest='logFile', action='store', help='Log file path')
    parser.add_argument('-e', '--log-level', dest='logLevel', action='store',
                        help='Log level DEBUG, INFO, WARNING, ERROR', default='INFO')

    parser.add_argument('-g', '--debug', dest='debug', action='store_true', help='Display log on console')

    args = parser.parse_args()

    # Start main process loop
    process(args)


if __name__ == "__main__":
    main()
