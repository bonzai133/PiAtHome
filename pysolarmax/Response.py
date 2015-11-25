# -*- coding: utf-8 -*-

#===============================================================================
# Response
#===============================================================================
class Response:
    def __init__(self, respData):
        self.body = ""
        self.AddBlock(respData)
        
    def AddBlock(self, respData):
        logger.debug("AddBlock: %s" % respData)
        
        parts = respData.split("|")
        
        #self.header = parts[0]
        self.body += parts[1]
        #self.checksum = parts[2]

        #Parse body if it exists
        if self.body:
            parts = self.body.split(':')
            
            if len(parts) < 2:
                print RED + "Error in body: %s" % self.body + ENDC
                logger.error("Error in body: %s" % self.body)

                self.port = 0
                self.data = ""
                self.cmdList = []
            else:
                self.port = parts[0]
                self.data = parts[1]
                
                #separate each command response
                self.cmdList = self.data.split(';')

    def ParseCommandResponse(self):
        rsp = {}
        
        logger.debug("cmdList: %s" % repr(self.cmdList))
        for cmd in self.cmdList:
            if '=' in cmd:
                cmd_array = cmd.split('=')
                key = cmd_array[0]
                value = cmd_array[1]
            
                rsp[key] = value.split(",")
            else:
                rsp['return'] = cmd
        
        #Return a dictionary with a list of values for each received command
        return rsp
