# -*- coding: utf-8 -*-

#===============================================================================
# Request
#===============================================================================
class Request:
    GET = "64"
    SET = "C8"
    
    def __init__(self, cmdList, way=GET, attr=None, fFormat=None):
        self.srcAddr = "FB"
        self.destAddr = "01"
        self.way = way
        
        #Check if we have a list or a single command
        if not isinstance(cmdList, str):
            self.cmdName = ";".join(cmdList)
        else:
            self.cmdName = cmdList
            
        self.attr = attr
        self.fFormat = fFormat
        
    def CheckSum16(self, sText):
        '''Calculate the cheksum 16 of the given argument'''
        #Convert string to char array
        cArray = list(sText)
        iSum = 0
        for c in cArray:
            iSum += ord(c)
            iSum %= 2 ** 16
            
        return iSum
                
    def BuildCommand(self):
        #Build body
        if(self.way == Request.GET):
            #Build a GET command
            sBody = "%s:%s" % (self.way, self.cmdName)
        else:
            #Build a SET command
            if(self.fFormat):
                sFormattedAttr = self.fFormat(self.attr)
            else:
                sFormattedAttr = self.attr
            
            sBody = "%s:%s=%s" % (self.way, self.cmdName, sFormattedAttr)
          
        #Calculate length
        totalLen = len("{00;00;00||0000}") + len(sBody)
        
        #Format message and calculate checksum
        msg = "%s;%s;%02X|%s|" % (self.srcAddr, self.destAddr, totalLen, sBody)
        checksum = self.CheckSum16(msg)
        
        return "{%s%04X}" % (msg, checksum)
