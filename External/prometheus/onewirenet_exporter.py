import logging
import argparse
import configparser
import time
from pyownet import protocol

import os
os.environ['PROMETHEUS_DISABLE_CREATED_SERIES'] = "True"

from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily
from prometheus_client import REGISTRY, GC_COLLECTOR, PLATFORM_COLLECTOR

REGISTRY.unregister(GC_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
# REGISTRY.unregister(PROCESS_COLLECTOR)


class OneWireNetCollector(object):
    def __init__(self, config) -> None:
        self.owserver = config["MAIN"]['owserver']
        self.owport = config["MAIN"].getint('owport')

        self.config = config

    def collect(self):
        # Valid oid
        owproxy = protocol.proxy(host=self.owserver, port=self.owport)
        valid_oids = owproxy.dir()

        # Read values
        for oid, attributes in self.config.items():
            if oid[:3] == 'id:':
                if f"/{oid[3:]}/" in valid_oids:
                    try:
                        metrics = self.read_values(owproxy, oid[3:], attributes)

                        for k, v in metrics.items():
                            g1 = GaugeMetricFamily(v[0], 'One wire sensor info', labels=['family', 'id'])
                            g1.add_metric([v[1], v[2]], v[3])
                            yield g1

                    except Exception as e:
                        logging.error("Collect OneWireNet error: %s", e)
                else:
                    logging.warning("Invalid sensor: %s", oid)

    def read_values(self, owproxy, oid, attributes):
        metrics = {}
        for attrib, alias in attributes.items():
            max_val = None
            try:
                if '|' in alias:
                    alias_max = alias.split('|')
                    max_val = float(alias_max[1])
                    alias = alias_max[0]
            except Exception:
                logging.error("Can't split alias %s for max value" % alias)

            try:
                family = owproxy.read(f'/{oid}/type').decode()
                id = owproxy.read(f'/{oid}/id').decode()
                value = float(owproxy.read(f'/{oid}/{alias}').decode().strip())

                key = f"{family}_{id}_{alias}"

                # Do not return value if it exceed max val
                if max_val is None or value < max_val:
                    metrics[key] = (alias, family, id, value)

            except AttributeError as e:
                logging.error("Attribute not found: %s", e)
            except Exception as e:
                logging.error("Exception: %s", e)

        return metrics


def register(args, config):
    # Start Prometheus serveur and register gauges in service mode only
    logging.info("Starting Prometheus exporter")
    start_http_server(args.metrics_port)

    # Create metrics
    REGISTRY.register(OneWireNetCollector(config))


def process(args):
    '''
    Main loop processownet
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
    register(args, config)

    # Check if we run as a service
    while True:
        time.sleep(10000)


def main():
    '''
    Main entry point

    :return:
    '''

    # Get parameters
    parser = argparse.ArgumentParser(description='Read values from OneWireNet interface')

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
