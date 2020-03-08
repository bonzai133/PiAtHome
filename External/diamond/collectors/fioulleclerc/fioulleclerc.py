#!/usr/bin/env python
# -*- coding: utf-8 -*-

import diamond.collector
import lxml.html as LH
import requests


class FioulLeclercCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(FioulLeclercCollector, self).get_default_config_help()
        config_help.update({
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(FioulLeclercCollector, self).get_default_config()
        config.update({
            'path': 'fioul_leclerc',
            'url': 'https://www.eleclerc-serviceouest.com/nos-tarifs/',
        })
        return config

    def collect(self):
        """
        Overrides the Collector.collect method
        """
        url = self.config['url']

        value = self.get_fioul_price(url)

        if value > 0:
            self.publish("fioul", value, precision=3)
        else:
            self.log.error("Invalid price")

    def text(self, elt):
        return elt.text_content().replace(u'\xa0', u' ')

    def get_fioul_price(self, url):
        price = -1.0

        r = requests.get(url)
        root = LH.fromstring(r.content)

        for th in root.xpath('//div[@id="tableau1"]/div/table/thead/tr/th'):
            if u'FIOUL\nORDINAIRE' in self.text(th):
                break
        else:
            self.log.error("Fioul page has change (1): update script.")

        tds = root.xpath('//div[@id="tableau1"]/div/table/tbody/tr/td')
        for idx, td in enumerate(tds):
            if u"1 000 à 1 999 litres" in self.text(td):
                price = float(self.text(tds[idx + 2]).replace(',', '.'))
                break
        else:
            self.log.error("Fioul page has change (2): update script.")

        return price
