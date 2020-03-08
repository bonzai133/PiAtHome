# coding=utf-8

"""
The TeleinfoCollector collects data from teleinfo file

To configure which counter to read:

-  add section [id:$counterid] with attributes and aliases,

Author: Laurent Petit

"""

import diamond.collector
import os
import json

class TeleinfoCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(TeleinfoCollector, self).get_default_config_help()
        config_help.update({
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(TeleinfoCollector, self).get_default_config()
        config.update({
            'path': 'teleinfo',
            'teleinfo_path': '/var/run/shm/',
            'teleinfo_prefix': 'teleinfo_'
        })
        return config

    def collect(self):
        """
        Overrides the Collector.collect method
        """
        metrics = {}
        teleinfo_path = self.config['teleinfo_path']
        teleinfo_prefix = self.config['teleinfo_prefix']

        #Get file path from config
        for oid, attributes in self.config.iteritems():
            if oid[:3] == 'id:':
                teleinfo_file = os.path.join(teleinfo_path, teleinfo_prefix + oid[3:])
                
                try:
                    with open(teleinfo_file, 'r') as fp:
                        data = json.load(fp)
                        if 'ADCO' in data:
                            self.log.debug("Valid data found: %s" % repr(data))
                            self.read_values(data, attributes, metrics)
                except Exception, e:
                    self.log.error("Collect TeleinfoCollector error: %s", e)
        
        for fn, fv in metrics.iteritems():
            self.publish(fn, fv, precision=2)


    #===========================================================================
    # read_values : read values in json data
    #===========================================================================
    def read_values(self, data, attributes, metrics):
        for attrib, alias in attributes.iteritems():
            if attrib in data:
                key = '%s.%s' % (data['ADCO'], attrib)
                metrics[key] = float(data[attrib])
            else:
                self.log.error("Attribute %s not found: %s", attrib, e)

