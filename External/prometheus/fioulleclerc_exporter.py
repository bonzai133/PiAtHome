# Disable _created metrics
import os
os.environ['PROMETHEUS_DISABLE_CREATED_SERIES'] = "True"

import time
from prometheus_client import start_http_server, Gauge, Summary
from prometheus_client import REGISTRY, GC_COLLECTOR, PLATFORM_COLLECTOR, PROCESS_COLLECTOR

REGISTRY.unregister(GC_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
#REGISTRY.unregister(PROCESS_COLLECTOR)

import configparser

import lxml.html as LH
import requests
import logging

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s [%(levelname)s] %(message)s',)

REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

class FioulPageParser():
    def __init__(self, url) -> None:
        self.url = url
        self.error_gauge = None

    @REQUEST_TIME.time()
    def __call__(self):
        return self.get_fioul_price()

    def set_error_gauge(self, error_g):
        self.error_gauge = error_g
        self.unset_parse_error()

    def set_parse_error(self):
        if self.error_gauge is not None:
            self.error_gauge.set(1)

    def unset_parse_error(self):
        if self.error_gauge is not None:
            self.error_gauge.set(0)

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
            self.set_parse_error()
            return price

        # Search the line with "1 000 à 1 999 litres"
        tds = root.xpath('//div[@id="tableau1"]/div/table/tbody/tr/td')
        for idx, td in enumerate(tds):
            if u"1 000 à 1 999 litres" in self.text(td):
                price = float(self.text(tds[idx + 2]).replace(',', '.'))

                self.unset_parse_error()
                break
        else:
            logging.error("Fioul page has change (2): update script.")
            self.set_parse_error()

        return price

def register_prometheus_gauges(url):
    fioulPageParser = FioulPageParser(url)

    g = Gauge("fioul_standard_price_in_euros", "Price of standard fioul in Euros")
    g.set_function(fioulPageParser)

    error_g = Gauge("fioul_parser_error", "Is 1 if error parsing the page")
    fioulPageParser.set_error_gauge(error_g)


def load_config(config_filename):
    config = configparser.ConfigParser()
    config.read(config_filename)

    return config['DEFAULT']

if __name__ == "__main__":
    config = load_config(os.path.splitext(__file__)[0] + ".conf")
    if 'url' not in config or config['url'] == "":
        logging.error("Bad configuration: please set 'url'")
        exit(-1)

    start_http_server(8000)

    register_prometheus_gauges(config['url'])
    while True:
        time.sleep(10000)