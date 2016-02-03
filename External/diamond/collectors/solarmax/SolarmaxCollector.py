# coding=utf-8

"""
The SolarmaxCollector collects data from Solarmax Inverter using pysolarmax
You can configure any known command that returns numeric value

Author: Laurent Petit

#### Dependencies

 * pysolarmax
"""

import diamond.collector
from pysolarmax.Inverter import Inverter

class SolarmaxCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(SolarmaxCollector, self).get_default_config_help()
        config_help.update({
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(SolarmaxCollector, self).get_default_config()
        config.update({
            'path': 'Solarmax',
            'server': '192.168.0.123',
            'port': '12345',
        })
        return config

    def collect(self):
        """
        Overrides the Collector.collect method
        """
        metrics = {}
        server = self.config['server']
        port = int(self.config['port'])

        commands = {}
        for cmd, metric_name in self.config['metrics'].iteritems():
            commands[cmd] = metric_name

        try:
            self.read_values(server, port, commands, metrics)
        except Exception, e:
            self.log.error("Collect Solarmax collector error: %s", e)
        
        for fn, fv in metrics.iteritems():
            self.publish(fn, fv, precision=2)

    def read_values(self, server, port, commands, metrics):
        #Connect to inverter
        inverter = Inverter(server, port)
        
        if not inverter.connect():
            self.log.debug("Can't connect to inverter")
            return

        values = inverter.getValues(commands.keys())
        
        for key, cmd_obj in values.iteritems():
            metrics[commands[key] = cmd_obj.Value
