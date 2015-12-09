# -*- coding: utf-8 -*-

import socket
from Request import *
from Response import *
from datetime import datetime
from Format import Format
from DataConverter import DataConverter


#===============================================================================
# Logs
#===============================================================================
import logging
logger = logging.getLogger()


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
        try:
            my_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            my_sock.settimeout(15)
            self.m_sock = my_sock
            
            my_sock.connect((self.hostname, self.port))
            
            self.connected = True
        except IOError, e:
            logger.debug("Socket error: %s", e)
            self.connected = False
        
        return self.connected
    
    def disconnect(self):
        if self.m_sock is not None:
            self.m_sock.close()
            self.connected = False
            
        return True
    
    def _sendDataAndWaitResponse(self, cmdData):
        self.m_sock.send(cmdData)
        rspData = self.m_sock.recv(255)
        rsp = Response(rspData)
        while len(rspData) == 255:
            rspData = self.m_sock.recv(255)
            rsp.addBlock(rspData)

        return rsp
        
    def getValues(self, cmdList):
        logger.debug("getValues: %s" % repr(cmdList))
        convertedValues = {}
        
        try:
            cmd = Request(cmdList)
            cmdData = cmd.buildRequest()
        except Exception, e:
            logger.error("Build request command error: %s" % e)
            return convertedValues
    
        logger.debug("%d %s" % (len(cmdData), cmdData))
    
        if len(cmdData) < 128:
            rsp = self._sendDataAndWaitResponse(cmdData)
    
            commands = rsp.getCommands()
            
            dc = DataConverter()
            convertedValues.update(dc.convertValues(commands))
            
            #for cmd, values in commands.items():
                #dataConverter.TreatResponse(cmd, values)
            #    logger.debug("%s: %s" % (cmd, values))
        else:
            logger.error("Command too large")
            return convertedValues
            
        return convertedValues
            
    def setDateTime(self, datetimeToSet=datetime.now()):
        result = False
        #Request values
        logger.debug("setTimeToCurrentTime")
        cmd = Request(["SDAT"], way=Request.SET, attr=datetimeToSet, fFormat=Format.DateTime2Hex)
        cmdData = cmd.buildRequest()
    
        logger.debug("%d %s" % (len(cmdData), cmdData))
    
        if len(cmdData) < 128:
            rsp = self._sendDataAndWaitResponse(cmdData)
    
            commands = rsp.getCommands()
            if 'return' in commands.keys() and commands['return'] == 'Ok':
                logger.info("Inverter set to current time.")
                result = True
            else:
                logger.error("Inverter was NOT set to current time.")
        else:
            logger.error("Command too large")

        return result
