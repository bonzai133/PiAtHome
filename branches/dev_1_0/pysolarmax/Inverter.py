# -*- coding: utf-8 -*-

import socket
import logging

#===============================================================================
# Logs
#===============================================================================
log = logging.getLogger()


#===============================================================================
# Inverter
#===============================================================================
class Inverter():
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.m_sock = None
        self.connected = False
    
    def __del__(self):
        self.disconnect()
    
    def connect(self):
        res = True
        try:
            my_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            my_sock.settimeout(15)
            self.m_sock = my_sock
            
            my_sock.connect((self.hostname, self.port))
            
            self.connected = True
        except IOError, e:
            log.debug("Socket error: %s", e)
            self.connected = False
        
        return self.connected
    
    def disconnect(self):
        if self.m_sock is not None:
            self.m_sock.close()
            self.connected = False
            
        return True
    
    def getValues(self):
        pass
    
    def setDateTime(self):
        pass
