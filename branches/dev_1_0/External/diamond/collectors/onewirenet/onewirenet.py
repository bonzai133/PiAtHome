# coding=utf-8

"""
The OneWireNetCollector collects data from 1-Wire Server

You can configure which sensors are read in two way:

-  add section [scan] with attributes and aliases,
   (collector will scan owfs to find attributes)

or

- add sections with format id:$SENSOR_ID

See also: http://owfs.org/
Author: Laurent Petit

#### Dependencies

 * owser
 * ownet

"""

import diamond.collector
import ownet

class OneWireNetCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(OneWireNetCollector, self).get_default_config_help()
        config_help.update({
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(OneWireNetCollector, self).get_default_config()
        config.update({
            'path': 'ownet',
            'owserver': 'localhost',
            'owport': '4304',
        })
        return config

    def collect(self):
        """
        Overrides the Collector.collect method
        """
        metrics = {}
        server = self.config['owserver']
        port = int(self.config['owport'])

        #if 'scan' in self.config:
        #    for ld in os.listdir(self.config['owfs']):
        #        if '.' in ld:
        #            self.read_values(ld, self.config['scan'], metrics)

        for oid, attributes in self.config.iteritems():
            if oid[:3] == 'id:':
                try:
                    self.read_values(server, port, oid[3:], attributes, metrics)
                except Exception, e:
                    self.log.error("Collect OneWireNet error: %s", e)
        
        for fn, fv in metrics.iteritems():
            self.publish(fn, fv, precision=2)

    def read_values(self, server, port, oid, attributes, metrics):
        r = ownet.Sensor('/%s' % oid, server=server, port=port)

        for attrib, alias in attributes.iteritems():
            max_val = None
            try:
                if '|' in alias:
                    alias_max = alias.split('|')
                    max_val = float(alias_max[1])
                    alias = alias_max[0]
            except:
                self.log.error("Can't split alias %s for max value" % alias)

            try:
                key = '%s_%s.%s' % (getattr(r, 'family'), getattr(r, 'id'), alias)
                value = getattr(r, attrib)

                if max_val is None or value < max_val:
                    metrics[key] = value
            except AttributeError, e:
                self.log.error("Attribute not found: %s", e)

