# coding=utf-8

"""
This collector retrieve status from freebox v5 and send some metrics
"""

import diamond.collector
import freebox_v5_status.freeboxstatus

class FreeboxStatusCollector(diamond.collector.Collector):
    def get_default_config_help(self):
        config_help = super(FreeboxStatusCollector, self).get_default_config_help()
        config_help.update({})
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(FreeboxStatusCollector, self).get_default_config()
        config.update({
            'path': 'Freebox',
        })
        return config

    def collect(self):
        #Get freebox status
        try:
            fbx = freebox_v5_status.freeboxstatus.FreeboxStatus()
        except Exception, e:
            self.log.error("Can't get Freebox status: %s" % e)
            return

        # Publish Metric Name and value
        try:
            eth = fbx.status['network']['interfaces']['ethernet']
            self.publish('ethernet.up', eth['up'] or 0)
            self.publish('ethernet.down', eth['down'] or 0)
        except Exception, e:
            self.log.error("Exception while collecting ethernet info: %s" % e)

	try:
            switch = fbx.status['network']['interfaces']['switch']
            self.publish('switch.up', switch['up'] or 0)
            self.publish('switch.down', switch['down'] or 0)
        except Exception, e:
            self.log.error("Exception while collecting switch info: %s" % e)

        try:
            wan = fbx.status['network']['interfaces']['WAN']
            self.publish('wan.up', wan['up'] or 0)
            self.publish('wan.down', wan['down'] or 0)
        except Exception, e:
            self.log.error("Exception while collecting WAN info: %s" % e)


