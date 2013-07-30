#!/usr/bin/env python
#-*-coding: utf-8 -*-

import argparse, socket, re
from datetime import *

class Format:
    @staticmethod
    def DateTime2Hex(xTime):
        #now = datetime.now()
        seconds = xTime.hour * 3600 + xTime.minute * 60 + xTime.second
        hex_datetime = '%03X%02X%02X,%04X' % (xTime.year, xTime.month, xTime.day, seconds)
        return hex_datetime

class Command():
    def __init__(self, Name, Descr, DataConvert, Output):
        self.Name = Name
        self.Descr = Descr
        self.DataConvert = DataConvert
        self.Output = Output
        self.Value = None
        
    def __str__(self):
        return "%s : %s" % (self.Name, self.Descr)





class DataConverter:
    m_Status = {
        20001:"En service",
        20002:"Rayonnement trop faible",
        20003:"Démarrer",
        20004:"Exploitation MPP",
        20005:"Ventilateur tourne",
        20006:"Exploitation Puissance max",
        20007:"Limitation température",
        20008:"Sur secteur",
        20009:"Courant DC limité",
        20010:"Courant AC limité",
        20011:"Mode test",
        20012:"Télécommandé",
        20013:"Retard au démarrage",
        20110:"Tension cct interm. trop élevée",
        20111:"Surtension",
        20112:"Surcharge",
        20114:"Courant de fuite trop élevé",
        20115:"Pas de secteur",
        20116:"Fréq. secteur trop élevée",
        20117:"Fréq. secteur trop basse",
        20118:"Fonctionnement en îlot",
        20119:"Mauvaise qualité du secteur",
        20122:"Tension secteur trop élevée",
        20123:"Tension secteur trop basse",
        20124:"Température trop élevée",
        20125:"Courant secteur dissym.",
        20126:"Erreur entrée ext. 1",
        20127:"Erreur entrée ext. 2",
        20129:"Sens de rotation incorrect",
        20130:"Faux type d’appareil",
        20131:"Commut. général hors",
        20132:"Diode de surtempérature",
        20134:"Ventilateur défectueux",
        20165:"Pas de secteur 2",}

    m_DeviceType = {
        2001:"SolarMax 2000 E",
        20:"SolarMax 20C",
        10210:"MaxMeteo",
        3001:"SolarMax 3000 E",
        25:"SolarMax 25C",
        10300:"MaxCount",
        4000:"SolarMax 4000 E",
        30:"SolarMax 30C",
        6000:"SolarMax 6000 E",
        35:"SolarMax 35C",
        2010:"SolarMax 2000C",
        50:"SolarMax 50C",
        3010:"SolarMax 3000C",
        80:"SolarMax 80C",
        4010:"SolarMax 4000C",
        100:"SolarMax 100C",
        4200:"SolarMax 4200C",
        300:"SolarMax 300C",
        6010:"SolarMax 6000 C",
        20100:"SolarMax 20S",
        20010:"SolarMax 2000 S",
        20110:"SolarMax 35S",
        20020:"SolarMax 3000 S",
        20030:"SolarMax 4200 S",
        20040:"SolarMax 6000 S",
        6010:"SolarMax 6000C"}
    
    @staticmethod 
    def convertSYS(values):
        code = values[0]
        try:
            retStr = DataConverter.m_Status[int(code, 16)]
        except KeyError:
            retStr = "Unknwon Status %d" % int(code, 16)
            
        return retStr
    
    @staticmethod 
    def convertType(values):
        value = values[0]
        try:
            retStr =  DataConverter.m_DeviceType[int(value,16)]
        except KeyError:
            retStr = "Unknwon Type %d" % int(value, 16)
            
        return retStr
    
    @staticmethod
    def convertDate(values):
        #7DB0206 -> 2011-02-06
        m = re.split("(.+)(.{2})(.{2})", values[0])
        
        #print "Date ", repr(m)
        year = str(int(m[1], 16))
        month = str(int(m[2], 16))
        day = str(int(m[3], 16))
        
        return year + "-" + month + "-" + day

    @staticmethod 
    def convertD2(values):
        value = values[0]
        return str(int(value, 16)/2.0)
    
    @staticmethod 
    def convertD10(values):
        value = values[0]
        return str(int(value, 16)/10.0)
    
    @staticmethod 
    def convertD100(values):
        value = values[0]
        return str(int(value, 16)/100.0)
        
    @staticmethod 
    def convertX1(values):
        value = values[0]
        return str(int(value, 16))
    @staticmethod 
    def convertX10(values):
        value = values[0]
        return str(int(value, 16)*10)
    @staticmethod 
    def convertX100(values):
        value = values[0]
        return str(int(value, 16)*100)
    @staticmethod 
    def convertX500(values):
        value = values[0]
        return str(int(value, 16)*500)       
             
    m_Commands = {
                  'SYS':Command('SYS', 'Operation State', convertSYS, None),
                  'ADR':Command('ADR', 'Address', convertX1, None),
                  'TYP':Command('TYP', 'Type', convertType, None),
                  'SWV':Command('SWV', 'Software version', convertD10, None),
                  'BDN':Command('BDN', 'Build number', convertX1, None),
                  'DDY':Command('DDY', 'Date day', convertX1, None),
                  'DMT':Command('DMT', 'Date month', convertX1, None),
                  'DYR':Command('DYR', 'Date year', convertX1, None),
                  'THR':Command('THR', 'Time hours', convertX1, None),
                  'TMI':Command('TMI', 'Time minutes', convertX1, None),

                  'KHR':Command('KHR', 'Operating hours', convertX1, None),
                  'KDY':Command('KDY', 'Energy today [Wh]', convertX100, None),
                  'KLD':Command('KLD', 'Energy yesterday [Wh]', convertX100, None),
                  'KMT':Command('KMT', 'Energy this month [kWh]', convertX1, None),
                  'KLM':Command('KLM', 'Energy last month [kWh]', convertX1, None),
                  'KYR':Command('KYR', 'Energy this year [kWh]', convertX1, None),
                  'KLY':Command('KLY', 'Energy last year [kWh]', convertX1, None),
                  'KT0':Command('KT0', 'Energy total [kWh]', convertX1, None),
                  
                  'LAN':Command('LAN', 'Language', convertX1, None),

                  'UDC':Command('UDC', 'DC voltage [V]', convertD10, None),
                  'UL1':Command('UL1', 'AC voltage [V]', convertD10, None),
                  'IDC':Command('IDC', 'DC current [A]', convertD100, None),
                  'IL1':Command('IL1', 'AC current [A]', convertD100, None),
                  'PAC':Command('PAC', 'AC power [W]', convertD2, None),
                  'PIN':Command('PIN', 'Power installed [W]', convertD2, None),

                  'PRL':Command('PRL', 'AC power [%]', convertX1, None),
                  'CAC':Command('CAC', 'Start ups', convertX1, None),
                  'FRD':Command('FRD', 'First run date', convertDate, None),

                  'TKK':Command('TKK', 'Temperature Heat Sink', convertX1, None),
                  'TNF':Command('TNF', 'AC Frequency', convertD100, None),

      }

    
    def TreatResponse(self, command, values):
        try:
            #Call a static method need to use the __get__ method
            self.m_Commands[command].Value = \
                self.m_Commands[command].DataConvert.__get__(None, DataConverter)(values)
            
            #print self.m_Commands[command].Value
            
        except KeyError:
            print "Unknown command '%s' = %s" % (command, values)
            
    def GetCurrentValue(self, command):
        cmd = self.m_Commands[command]
        
        print "%s : %s" % (cmd, cmd.Value)
    

class Response:
        
    def __init__(self, respData):
        parts = respData.split("|")
        
        self.header = parts[0] 
        self.body = parts[1]
        self.checksum = parts[2]

        #Parse body if it exists
        if self.body: 
            parts = self.body.split(':')
            
            self.port = parts[0]
            self.data = parts[1]
            
            #separate each command response
            self.cmdList = self.data.split(';')
        
    def ParseCommandResponse(self):
        rsp = {}
        for cmd in self.cmdList:
            key = cmd.split('=')[0]
            value = cmd.split('=')[1]
            
            rsp[key] = value.split(",")
        
        #Return a dictionary with a list of values for each received command 
        return rsp


class Request:
    GET = "64"
    SET  ="C8"
    
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
            iSum %= 2**16
            
        return iSum
                
    def BuildCommand(self):
        #Build body
        if(self.way==Request.GET):
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
        
        


def main():
    #Get parameters
    parser = argparse.ArgumentParser(description='Request values to Solarmax inverter')
    parser.add_argument('-H',  '--host', dest='hostname', action='store',  help='Host name',  default='192.168.0.123')
    parser.add_argument('-p',  '--port', dest='port', type=int,  action='store',  help='Port value',  default='12345')

    args = parser.parse_args()
    
    #Connect to inverter
    #Create socket and connect
    my_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_sock.connect((args.hostname,  args.port))
    
    #TODO : treat connection errors
    print "Connected to %s:%d" % (args.hostname,  args.port)
    
    #Request values
    
    
    #Display values
    
        
    #Store values
    
    
    #Close the socket
    my_sock.close()
    print "Disconnected\n"

def testCmd():
    cmd = Request(["SAL"])
    print cmd.BuildCommand()
    
    cmd = Request("SAL")
    print cmd.BuildCommand()

    cmd = Request(["SAL","SYS"])
    print cmd.BuildCommand()
    
    cmd = Request(["SDAT"], way=Request.SET, attr=datetime.now(), fFormat=Format.DateTime2Hex)
    print cmd.BuildCommand()
    
def testRsp():
    #rsp = Response("{01;FB;23|64:SAL=0;SYS=4E24,0|075F}")
    #rsp = Response("{01;FB;48|64:SDAT=7DC0219,E050;SNM=FF,FF,FF,0;SRD=0;SRS=0;TCP=3039|107D}")
    rsp = Response("{01;FB;3B|64:TNF=138C;UDC=CDD;UGD=766;UL1=92B;UM1=928|0D73}")
    cmdDict = rsp.ParseCommandResponse()
    
    dc = DataConverter()
    for cmd, values in cmdDict.items():
        dc.TreatResponse(cmd, values)

    rsp = Response("{01;FB;38|64:IL1=2D1;PAC=D16;PDC=DD2;PRL=3A;TKK=2C|0CC1}")
    cmdDict = rsp.ParseCommandResponse()
    for cmd, values in cmdDict.items():
        dc.TreatResponse(cmd, values)
    
    dc.GetCurrentValue("TNF")
    dc.GetCurrentValue("UL1")
    dc.GetCurrentValue("IL1")
    

if __name__ == "__main__":
    #main()
    #testCmd()
    
    #TODO exception socket
    #File "./Solarmax.py", line 532, in main
    #s.connect((HOST, PORT))
    #File "/usr/lib/python2.7/socket.py", line 224, in meth
    #return getattr(self._sock,name)(*args)
    #socket.error: [Errno 101] Network is unreachable
    
    #TODO : interpréter les réponses
    testRsp()
    
