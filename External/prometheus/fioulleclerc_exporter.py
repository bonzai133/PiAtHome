# Disable _created metrics
import os
os.environ['PROMETHEUS_DISABLE_CREATED_SERIES'] = "True"

import logging
import time
import argparse
import configparser
import lxml.html as LH
import requests

from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily
from prometheus_client import REGISTRY, GC_COLLECTOR, PLATFORM_COLLECTOR

REGISTRY.unregister(GC_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
# REGISTRY.unregister(PROCESS_COLLECTOR)


class FioulLeclercCollector(object):
    def __init__(self, config) -> None:
        self.url = config['url']
        self.error_gauge = None

    def collect(self):
        # Read values
        values = self.get_fioul_price()

        if values != -1.0:
            yield GaugeMetricFamily("fioul_standard_price_in_euros", "Price of standard fioul in Euros",
                                    value=values)
            yield GaugeMetricFamily("fioul_parser_error", "Is 1 if error parsing the page",
                                    value=0)
        else:
            yield GaugeMetricFamily("fioul_parser_error", "Is 1 if error parsing the page",
                                    value=1)

    def text(self, elt):
        return elt.text_content().replace(u'\xa0', u' ')

    def get_fioul_price(self):
        price = -1.0

        r = requests.get(self.url)
        root = LH.fromstring(r.content)

        # check if "tableau1" header contains FIOUL ORDINAIRE
        for th in root.xpath('//div[@id="tableau1"]/div/table/thead/tr/th'):
            if u'FIOUL\nORDINAIRE' in self.text(th):
                break
        else:
            logging.error("Fioul page has change (1): update script.")
            return price

        # Search the line with "1 000 à 1 999 litres"
        tds = root.xpath('//div[@id="tableau1"]/div/table/tbody/tr/td')
        for idx, td in enumerate(tds):
            if u"1 000 à 1 999 litres" in self.text(td):
                price = float(self.text(tds[idx + 2]).replace(',', '.'))
                break
        else:
            logging.error("Fioul page has change (2): update script.")
            return price

        return price


def register(args, config):
    # Start Prometheus serveur and register gauges in service mode only
    logging.info("Starting Prometheus exporter")
    start_http_server(args.metrics_port)

    # Create metrics
    REGISTRY.register(FioulLeclercCollector(config))


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
    parser = argparse.ArgumentParser(description='Prometheus exporter for Fioul Leclerc price')

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
