# coding=utf-8
"""
The PhilipsTvChannelCollector collects the current channel watched

"""

import os
import diamond.collector
import json
import urllib2

class PhilipsTvChannelCollector(diamond.collector.Collector):
    def get_default_config_help(self):
        config_help = super(PhilipsTvChannelCollector, self).get_default_config_help()
        config_help.update({})
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(PhilipsTvChannelCollector, self).get_default_config()
        config.update({
            'path': 'philips_TV',
            'philipstv': '127.0.0.1',
        })
        return config
        
    def collect(self):
        """
        Overrides the Collector.collect method
        """
        try:
            self.log.debug("Enter collect: %s" % self.config['philipstv'])
            value = self.getCurrentChannel()

            self.log.debug("Found channel %d" % value)
            self.publish('channel', value, precision=0)

            #Send on/off status
            #if value != 0:
            #    self.publish('onStatus', 1, precision=0)
            #else:
            #    self.publish('onStatus', 0, precision=0)

        except Exception, e:
            self.log.error("Exception while collecting : %s" % e)
    
    #Get the response to the given command
    def queryTv(self, cmd):
        TV_URL_FORMAT = 'http://%s:1925/1/%s'

        respDoc = None
        url = TV_URL_FORMAT % (self.config['philipstv'], cmd)
        try:
            resp = urllib2.urlopen(url)
            respDoc = json.load(resp)
        except urllib2.HTTPError, e:
            self.log.debug('HTTPError = ' + str(e.code))
        except urllib2.URLError, e:
            self.log.debug('URLError = ' + str(e.reason))
        except httplib.HTTPException, e:
            self.log.debug('HTTPException')
        except Exception, e:
            self.log.debug('Exception = ' + str(e))
        
        return respDoc

    def getCurrentChannel(self):
        #Return value
        valueToReturn = 0
        
        #Get the current source
        cmd = "sources/current"
        source = self.queryTv(cmd)
 
        #Get the list of channels
        cmd = "channels"
        channels = self.queryTv(cmd)
        
        #Get the current channel
        cmd = "channels/current"
        channel = self.queryTv(cmd)
        
        if channels is not None and channel is not None and source is not None:
            try:
                if source['id'] == 'tv':
                    chId = channel['id']
                    if chId not in channels:
                        self.log.debug("Channel is not in the list" % chId)
                    else:
                        num = channels[chId]['preset']
                        name = channels[chId]['name']
                    
                        self.log.debug("Watching tv channel %s (%s)" % (num, name))
                        valueToReturn = int(num)
                else:
                    self.log.debug("Watching another source : %s" % source['id'])
                    valueToReturn = -1
            except Exception, e:
                self.log.debug('GetCurrentChannel exception = ' + str(e))
        
        self.log.debug("Return %d" % valueToReturn)        
        return valueToReturn

