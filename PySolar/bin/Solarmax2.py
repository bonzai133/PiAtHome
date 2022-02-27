#!/usr/bin/env python
#-*-coding: utf-8 -*-

import os
import logging
import logging.config

import argparse
import socket
import re
from datetime import *
from time import *
from SqliteDBManager import *

#Logger
try:
    ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
    LOGCONF_PATH = os.path.join(ROOT_PATH, 'logging_pysolarmax.conf')
    
    logging.config.fileConfig(LOGCONF_PATH)
except Exception as e:
    print("Can't read logger configuration: %s" % e)
logger = logging.getLogger(__name__)

#Output colors
RED = '\033[91m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
BLUE = '\033[94m'
ENDC = '\033[0m'


#===============================================================================
# Format convertion
#===============================================================================
class Format:
    @staticmethod
    def DateTime2Hex(xTime):
        #now = datetime.now()
        seconds = xTime.hour * 3600 + xTime.minute * 60 + xTime.second
        hex_datetime = '%03X%02X%02X,%04X' % (xTime.year, xTime.month, xTime.day, seconds)
        return hex_datetime


#===============================================================================
# Command class
#===============================================================================
class Command():
    def __init__(self, Name, Descr, DataConvert, Output):
        self.Name = Name
        self.Descr = Descr
        self.DataConvert = DataConvert
        self.Output = Output
        self.Value = None
        
    def __str__(self):
        return "%s : %s" % (self.Name, self.Descr)


#===============================================================================
# DataConverter
#===============================================================================
class DataConverter:
    def __init__(self, dbm=None):
        self.m_sqlRequestList = []
        self.m_dbm = dbm

    m_Status = {
        20001: "En service",
        20002: "Rayonnement trop faible",
        20003: "Démarrer",
        20004: "Exploitation MPP",
        20005: "Ventilateur tourne",
        20006: "Exploitation Puissance max",
        20007: "Limitation température",
        20008: "Sur secteur",
        20009: "Courant DC limité",
        20010: "Courant AC limité",
        20011: "Mode test",
        20012: "Télécommandé",
        20013: "Retard au démarrage",
        20110: "Tension cct interm. trop élevée",
        20111: "Surtension",
        20112: "Surcharge",
        20114: "Courant de fuite trop élevé",
        20115: "Pas de secteur",
        20116: "Fréq. secteur trop élevée",
        20117: "Fréq. secteur trop basse",
        20118: "Fonctionnement en îlot",
        20119: "Mauvaise qualité du secteur",
        20122: "Tension secteur trop élevée",
        20123: "Tension secteur trop basse",
        20124: "Température trop élevée",
        20125: "Courant secteur dissym.",
        20126: "Erreur entrée ext. 1",
        20127: "Erreur entrée ext. 2",
        20129: "Sens de rotation incorrect",
        20130: "Faux type d’appareil",
        20131: "Commut. général hors",
        20132: "Diode de surtempérature",
        20134: "Ventilateur défectueux",
        20165: "TODO Error 20165",
        20173: "Tension secteur trop basse (?)",
}

    m_DeviceType = {
        2001: "SolarMax 2000 E",
        20: "SolarMax 20C",
        10210: "MaxMeteo",
        3001: "SolarMax 3000 E",
        25: "SolarMax 25C",
        10300: "MaxCount",
        4000: "SolarMax 4000 E",
        30: "SolarMax 30C",
        6000: "SolarMax 6000 E",
        35: "SolarMax 35C",
        2010: "SolarMax 2000C",
        50: "SolarMax 50C",
        3010: "SolarMax 3000C",
        80: "SolarMax 80C",
        4010: "SolarMax 4000C",
        100: "SolarMax 100C",
        4200: "SolarMax 4200C",
        300: "SolarMax 300C",
        6010: "SolarMax 6000 C",
        20100: "SolarMax 20S",
        20010: "SolarMax 2000 S",
        20110: "SolarMax 35S",
        20020: "SolarMax 3000 S",
        20030: "SolarMax 4200 S",
        20040: "SolarMax 6000 S",
        6010: "SolarMax 6000C"}
    
    @staticmethod
    def convertSYS(values):
        code = values[0]
        try:
            retStr = DataConverter.m_Status[int(code, 16)]
        except KeyError:
            retStr = YELLOW + "Unknwon Status %d" % int(code, 16) + ENDC
            
        return retStr
    
    @staticmethod
    def convertError(values):
        logger.debug("ConvertError: %s" % values)

        date = DataConverter.convertDate([values[0]])
        time = DataConverter.convertTime([values[1]])
        
        key = int(values[2], 16)
        if key in DataConverter.m_Status:
            error = DataConverter.m_Status[key]
        else:
            logger.warning("Unknown error (%s)" % key)
            error = YELLOW + "Unknown error (%s)" % key + ENDC
        
        return (date, time, key, error)

    @staticmethod
    def convertType(values):
        value = values[0]
        try:
            retStr = DataConverter.m_DeviceType[int(value, 16)]
        except KeyError:
            logger.warning("Unknwon Type %d" % int(value, 16))
            retStr = YELLOW + "Unknwon Type %d" % int(value, 16) + ENDC
            
        return retStr
    
    @staticmethod
    def convertDate(values):
        #7DB0206 -> 2011-02-06
        m = re.split("(.+)(.{2})(.{2})", values[0])
        
        year = int(m[1], 16)
        month = int(m[2], 16)
        day = int(m[3], 16)
        
        return "%04d-%02d-%02d" % (year, month, day)

    @staticmethod
    def convertTime(values):
        return strftime('%H:%M:%S', gmtime(int(values[0], 16)))

    @staticmethod
    def convertD2(values):
        value = values[0]
        return str(int(value, 16) / 2.0)
    
    @staticmethod
    def convertD10(values):
        value = values[0]
        return str(int(value, 16) / 10.0)
    
    @staticmethod
    def convertD100(values):
        value = values[0]
        return str(int(value, 16) / 100.0)
        
    @staticmethod
    def convertX1(values):
        value = values[0]
        return str(int(value, 16))
    
    @staticmethod
    def convertX10(values):
        value = values[0]
        return str(int(value, 16) * 10)
    
    @staticmethod
    def convertX100(values):
        value = values[0]
        return str(int(value, 16) * 100)
    
    @staticmethod
    def convertX500(values):
        value = values[0]
        return str(int(value, 16) * 500)

    @staticmethod
    def convertDateEnergy(values):
        #7DB0112,1B,11F6,51 -> date, total watt, peak watt, hours sunshine
        date = DataConverter.convertDate([values[0]])
        total = DataConverter.convertD10([values[1]])
        peak = DataConverter.convertD2([values[2]])
        hours = DataConverter.convertD10([values[3]])

        #return date + " : " + total + " kWh, " + peak + " W peak, " + hours + " hours"
        return (date, total, peak, hours)

    def OutputPrint(self, cmd):
        print("%s = %s" % (cmd, cmd.Value))

    def OutputRealtime(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))
        print("%s = %s" % (cmd, cmd.Value))
        #Build request
        sqlRequest = 'REPLACE INTO Realtime '
        sqlRequest += '(key, value, desc) '
        sqlRequest += 'VALUES ("%s", "%s", "%s")' % (cmd.Name, cmd.Value, cmd.Descr)

        logger.debug("Request generated: %s" % sqlRequest)

        self.m_sqlRequestList.append(sqlRequest)

    def OutputStatistics(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))
        print("%s = %s" % (cmd, cmd.Value))
        #Build request
        sqlRequest = 'REPLACE INTO Statistics '
        sqlRequest += '(key, value, desc) '
        sqlRequest += 'VALUES ("%s", "%s", "%s")' % (cmd.Name, cmd.Value, cmd.Descr)

        logger.debug("Request generated: %s" % sqlRequest)

        self.m_sqlRequestList.append(sqlRequest)
        
    def OutputError(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))
        print("%s = %s" % (cmd, cmd.Value))

        #Split values
        (date_str, time_str, errCode, desc) = cmd.Value

        #Build request
        sqlRequest = 'REPLACE INTO ErrorsHistory '
        sqlRequest += '(datetime, errCode, desc) '
        sqlRequest += 'VALUES ("%s %s", "%s", "%s")' % (date_str, time_str, errCode, desc)

        logger.debug("Request generated: %s" % sqlRequest)

        self.m_sqlRequestList.append(sqlRequest)

    def OutputStatsYear(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))
        #Split values
        (date_str, energy, peak, hours) = cmd.Value

        #Format date
        date_array = date_str.split("-")
        
        year = date_array[0]
        month = "01"
        day = "01"

        date = "%s-%s-%s" % (year, month, day)

        #year 2000 indicate an empty data
        if year != "2000":
            #Build request
            sqlRequest = 'REPLACE INTO EnergyByYear '
            sqlRequest += '(date, year, energy, peak, hours) '
            sqlRequest += 'VALUES ("%s", "%s", "%s", "%s", "%s")' % (date, year, energy, peak, hours)

            logger.debug("Request generated: %s" % sqlRequest)

            self.m_sqlRequestList.append(sqlRequest)

    def OutputStatsMonth(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))

        #Split values
        (date_str, energy, peak, hours) = cmd.Value

        #Format date
        date_array = date_str.split("-")
        
        year = date_array[0]
        month = date_array[1]
        day = "01"

        date = "%s-%s-%s" % (year, month, day)

        #year 2000 indicate an empty data
        if year != "2000":
            #Build request
            sqlRequest = 'REPLACE INTO EnergyByMonth '
            sqlRequest += '(date, year, month, energy, peak, hours) '
            sqlRequest += 'VALUES ("%s", "%s", "%s", "%s", "%s", "%s")' % (date, year, month, energy, peak, hours)

            logger.debug("Request generated: %s" % sqlRequest)

            self.m_sqlRequestList.append(sqlRequest)

    def OutputStatsDay(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))

        #Split values
        (date_str, energy, peak, hours) = cmd.Value

        #Format date
        date_array = date_str.split("-")
        
        year = date_array[0]
        month = date_array[1]
        day = date_array[2]

        #year 2000 indicate an empty data
        if year != "2000":
            #Build request
            sqlRequest = 'REPLACE INTO EnergyByDay '
            sqlRequest += '(date, year, month, day, energy, peak, hours) '
            sqlRequest += 'VALUES ("%s", "%s", "%s", "%s", "%s", "%s", "%s")' % (date_str, year, month, day, energy, peak, hours)

            logger.debug("Request generated: %s" % sqlRequest)

            self.m_sqlRequestList.append(sqlRequest)

    m_Commands = {
                  'SYS': Command('SYS', 'Operation State', convertSYS, OutputRealtime),
                  'ADR': Command('ADR', 'Address', convertX1, OutputPrint),
                  'TYP': Command('TYP', 'Type', convertType, OutputPrint),
                  'SWV': Command('SWV', 'Software version', convertD10, OutputPrint),
                  'BDN': Command('BDN', 'Build number', convertX1, OutputPrint),
                  'DDY': Command('DDY', 'Date day', convertX1, OutputPrint),
                  'DMT': Command('DMT', 'Date month', convertX1, OutputPrint),
                  'DYR': Command('DYR', 'Date year', convertX1, OutputPrint),
                  'THR': Command('THR', 'Time hours', convertX1, OutputPrint),
                  'TMI': Command('TMI', 'Time minutes', convertX1, OutputPrint),

                  'KHR': Command('KHR', 'Operating hours', convertX1, OutputStatistics),
                  'KDY': Command('KDY', 'Energy today [Wh]', convertX100, OutputStatistics),
                  'KLD': Command('KLD', 'Energy yesterday [Wh]', convertX100, OutputStatistics),
                  'KMT': Command('KMT', 'Energy this month [kWh]', convertX1, OutputStatistics),
                  'KLM': Command('KLM', 'Energy last month [kWh]', convertX1, OutputStatistics),
                  'KYR': Command('KYR', 'Energy this year [kWh]', convertX1, OutputStatistics),
                  'KLY': Command('KLY', 'Energy last year [kWh]', convertX1, OutputStatistics),
                  'KT0': Command('KT0', 'Energy total [kWh]', convertX1, OutputStatistics),
                  
                  'UDC': Command('UDC', 'DC voltage [V]', convertD10, OutputRealtime),
                  'UL1': Command('UL1', 'AC voltage [V]', convertD10, OutputRealtime),
                  'IDC': Command('IDC', 'DC current [A]', convertD100, OutputRealtime),
                  'IL1': Command('IL1', 'AC current [A]', convertD100, OutputRealtime),
                  'PAC': Command('PAC', 'AC power [W]', convertD2, OutputRealtime),
                  'PIN': Command('PIN', 'Power installed [W]', convertD2, OutputRealtime),
                  'PRL': Command('PRL', 'AC power [%]', convertX1, OutputRealtime),

                  'TKK': Command('TKK', 'Temperature Heat Sink', convertX1, OutputRealtime),
                  'TNF': Command('TNF', 'AC Frequency', convertD100, OutputRealtime),

                  'LAN': Command('LAN', 'Language', convertX1, OutputPrint),
                  'CAC': Command('CAC', 'Start ups', convertX1, OutputPrint),
                  'FRD': Command('FRD', 'First run date', convertDate, OutputPrint),

                  'EC00': Command('EC00', 'Error 00', convertError, OutputError),
                  'EC01': Command('EC01', 'Error 01', convertError, OutputError),
                  'EC02': Command('EC02', 'Error 02', convertError, OutputError),
                  'EC03': Command('EC03', 'Error 03', convertError, OutputError),
                  'EC04': Command('EC04', 'Error 04', convertError, OutputError),
                  'EC05': Command('EC05', 'Error 05', convertError, OutputError),
                  'EC06': Command('EC06', 'Error 06', convertError, OutputError),
                  'EC07': Command('EC07', 'Error 07', convertError, OutputError),
                  'EC08': Command('EC08', 'Error 08', convertError, OutputError),
                  'EC09': Command('EC09', 'Error 09', convertError, OutputError),
                  'EC10': Command('EC10', 'Error 10', convertError, OutputError),
                  'EC11': Command('EC11', 'Error 11', convertError, OutputError),
                  'EC12': Command('EC12', 'Error 12', convertError, OutputError),
                  'EC13': Command('EC13', 'Error 13', convertError, OutputError),
                  'EC14': Command('EC14', 'Error 14', convertError, OutputError),
                  'EC15': Command('EC15', 'Error 15', convertError, OutputError),
                  'EC16': Command('EC16', 'Error 16', convertError, OutputError),
                  'EC17': Command('EC17', 'Error 17', convertError, OutputError),
                  'EC18': Command('EC18', 'Error 18', convertError, OutputError),
                  'EC19': Command('EC19', 'Error 19', convertError, OutputError),

                  'DY00': Command('DY00', 'Energy by year', convertDateEnergy, OutputStatsYear),
                  'DY01': Command('DY01', 'Energy by year', convertDateEnergy, OutputStatsYear),
                  'DY02': Command('DY02', 'Energy by year', convertDateEnergy, OutputStatsYear),
                  'DY03': Command('DY03', 'Energy by year', convertDateEnergy, OutputStatsYear),
                  'DY04': Command('DY04', 'Energy by year', convertDateEnergy, OutputStatsYear),
                  'DY05': Command('DY05', 'Energy by year', convertDateEnergy, OutputStatsYear),
                  'DY06': Command('DY06', 'Energy by year', convertDateEnergy, OutputStatsYear),
                  'DY07': Command('DY07', 'Energy by year', convertDateEnergy, OutputStatsYear),
                  'DY08': Command('DY08', 'Energy by year', convertDateEnergy, OutputStatsYear),
                  'DY09': Command('DY09', 'Energy by year', convertDateEnergy, OutputStatsYear),

                  'DM00': Command('DM00', 'Energy by month', convertDateEnergy, OutputStatsMonth),
                  'DM01': Command('DM01', 'Energy by month', convertDateEnergy, OutputStatsMonth),
                  'DM02': Command('DM02', 'Energy by month', convertDateEnergy, OutputStatsMonth),
                  'DM03': Command('DM03', 'Energy by month', convertDateEnergy, OutputStatsMonth),
                  'DM04': Command('DM04', 'Energy by month', convertDateEnergy, OutputStatsMonth),
                  'DM05': Command('DM05', 'Energy by month', convertDateEnergy, OutputStatsMonth),
                  'DM06': Command('DM06', 'Energy by month', convertDateEnergy, OutputStatsMonth),
                  'DM07': Command('DM07', 'Energy by month', convertDateEnergy, OutputStatsMonth),
                  'DM08': Command('DM08', 'Energy by month', convertDateEnergy, OutputStatsMonth),
                  'DM09': Command('DM09', 'Energy by month', convertDateEnergy, OutputStatsMonth),
                  'DM10': Command('DM10', 'Energy by month', convertDateEnergy, OutputStatsMonth),
                  'DM11': Command('DM11', 'Energy by month', convertDateEnergy, OutputStatsMonth),

                  'DD00': Command('DD00', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD01': Command('DD01', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD02': Command('DD02', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD03': Command('DD03', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD04': Command('DD04', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD05': Command('DD05', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD06': Command('DD06', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD07': Command('DD07', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD08': Command('DD08', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD09': Command('DD09', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD10': Command('DD10', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD11': Command('DD11', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD12': Command('DD12', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD13': Command('DD13', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD14': Command('DD14', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD15': Command('DD15', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD16': Command('DD16', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD17': Command('DD17', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD18': Command('DD18', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD19': Command('DD19', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD20': Command('DD20', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD21': Command('DD21', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD22': Command('DD22', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD23': Command('DD23', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD24': Command('DD24', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD25': Command('DD25', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD26': Command('DD26', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD27': Command('DD27', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD28': Command('DD28', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD29': Command('DD29', 'Energy by day', convertDateEnergy, OutputStatsDay),
                  'DD30': Command('DD30', 'Energy by day', convertDateEnergy, OutputStatsDay),
      }
        
    def TreatResponse(self, command, values):
        try:
            #Call a static method need to use the __get__ method
            self.m_Commands[command].Value = \
                self.m_Commands[command].DataConvert.__get__(None, DataConverter)(values)
            
            logger.debug("TreatResponse: %s" % repr(self.m_Commands[command].Value))
            
        except KeyError:
            logger.error("TreatResponse: Unknown command '%s' = %s" % (command, values))
            print(RED + "Unknown command '%s' = %s" % (command, values) + ENDC)
            
    def GetCurrentValue(self, command):
        try:
            cmd = self.m_Commands[command]
            if cmd.Output is None:
                logger.warning("GetCurrentValue: No Output: %s = %s" % (cmd, cmd.Value))
                print(YELLOW + "No Output: %s = %s" % (cmd, cmd.Value) + ENDC)
            else:
                #Call output function
                self.m_Commands[command].Output.__get__(self, DataConverter)(cmd)

        except KeyError:
            logger.warning("GetCurrentValue: Unknown command %s" % command)
    
    def CommitDataToDb(self):
        if self.m_dbm.connectFailure == 0:
            for req in self.m_sqlRequestList:
                logger.debug("Will execute: %s" % req)
                self.m_dbm.ExecuteRequest(req)
            
            self.m_dbm.Commit()


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
                print(RED + "Error in body: %s" % self.body + ENDC)
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


#===============================================================================
# setTimeToCurrentTime
#===============================================================================
def setTimeToCurrentTime(my_sock, dataConverter):
    #Request values
    logger.debug("setTimeToCurrentTime")
    cmd = Request(["SDAT"], way=Request.SET, attr=datetime.now(), fFormat=Format.DateTime2Hex)
    cmdData = cmd.BuildCommand()

    logger.debug("%d %s" % (len(cmdData), cmdData))

    if len(cmdData) < 128:
        my_sock.send(cmdData)
        rspData = my_sock.recv(255)
        
        rsp = Response(rspData)
        while len(rspData) == 255:
            rspData = my_sock.recv(255)
            rsp.AddBlock(rspData)

        cmdDict = rsp.ParseCommandResponse()
        if 'return' in list(cmdDict.keys()) and cmdDict['return'] == 'Ok':
            print("Inverter set to current time.")
            logger.info("Inverter set to current time.")
        else:
            print(RED + "Inverter was NOT set to current time." + ENDC)
            logger.error("Inverter was NOT set to current time.")

    else:
        logger.error("Command too large")


#===============================================================================
# addLastUpdateInDb
#===============================================================================
def addLastUpdateInDb(dbm, action):
    table = None
    if dbm.connectFailure == 0:
        if action == "Stats":
            table = "Statistics"
        elif action == "Realtime":
            table = "Realtime"

        key = "LastUpdate"
        value = datetime.now().strftime("%s")
        descr = "Last Update"
        
        if table is not None:
            #Prepare request
            sqlRequest = 'REPLACE INTO %s ' % table
            sqlRequest += '(key, value, desc) '
            sqlRequest += 'VALUES ("%s", "%s", "%s")' % (key, value, descr)
            
            #Execute request
            logger.debug("Will execute: %s" % sqlRequest)
            dbm.ExecuteRequest(sqlRequest)
            
            dbm.Commit()
    
    
#===============================================================================
# requestAndPrintCommands
#===============================================================================
def requestAndPrintCommands(my_sock, dataConverter, cmds):
    #Request values
    logger.debug("requestAndPrintCommands: %s" % repr(cmds))
    cmd = Request(cmds)
    cmdData = cmd.BuildCommand()

    logger.debug("%d %s" % (len(cmdData), cmdData))

    if len(cmdData) < 128:
        my_sock.send(cmdData)
        rspData = my_sock.recv(255)
        rsp = Response(rspData)
        while len(rspData) == 255:
            rspData = my_sock.recv(255)
            rsp.AddBlock(rspData)

        cmdDict = rsp.ParseCommandResponse()

        for cmd, values in list(cmdDict.items()):
            dataConverter.TreatResponse(cmd, values)

        for cmd in cmds:
            dataConverter.GetCurrentValue(cmd)
    else:
        logger.error("Command too large")

GROUPS_COMMANDS = (
        #Infos software
        {'group': 'Infos software', 'cmds': (
        "ADR", "TYP", "SWV", "LAN",
        "CAC",
        "FRD",
        "BDN",),
        'action': 'Info'
        },

        #Date and Time
        {'group': 'Date and Time', 'cmds': (
        "DDY", "DMT", "DYR", "THR", "TMI", ),
        'action': 'Info'
        },

        #Stats Production
        {'group': 'Stats Production', 'cmds': (
        "KHR", "KDY", "KLD", "KMT", "KLM", "KYR", "KLY", "KT0", ),
        'action': 'Stats'
        },

        #Current values
        {'group': 'Current values', 'cmds': (
        "UDC", "UL1",
        "IDC", "IL1",
        "PAC", "PIN", "PRL",
        "TNF",

        "TKK",
        "SYS", ),
        'action': 'Realtime'
        },
 
        #Errors
        {'group': 'Errors1', 'cmds': (
        "EC00", "EC01", "EC02", "EC03", "EC04", "EC05", "EC06", "EC07", "EC08", "EC09", ),
        'action': 'History'
        },
        {'group': 'Errors2', 'cmds': (
        "EC10", "EC11", "EC12", "EC13", "EC14", "EC15", "EC16", "EC17", "EC18", "EC19",),
        'action': 'History'
        },

        #Stats by day
        {'group': 'Stats by day 1', 'cmds': (
        "DD00", "DD01", "DD02", "DD03", "DD04", "DD05", "DD06", "DD07", "DD08", "DD09",
        "DD10", "DD11", "DD12", "DD13", "DD14", "DD15",),
        'action': 'History'
        },
        {'group': 'Stats by day 2', 'cmds': (
        "DD15", "DD16", "DD17", "DD18", "DD19",
        "DD20", "DD21", "DD22", "DD23", "DD24", "DD25", "DD26", "DD27", "DD28", "DD29",
        "DD30",),
        'action': 'History'
        },

        #Stats by month
        {'group': 'Stats by month', 'cmds': (
        "DM00", "DM01", "DM02", "DM03", "DM04", "DM05", "DM06", "DM07", "DM08", "DM09", "DM10", "DM11", ),
        'action': 'History'
        },

        #Stats by year
        {'group': 'Stats by year', 'cmds': (
        "DY00", "DY01", "DY02", "DY03", "DY04", "DY05", "DY06", "DY07", "DY08", "DY09", ),
        'action': 'History'
        },
        
        #Tests
        {'group': 'Tests', 'cmds': (
        "DDY", "DMT", "DYR", "THR", "TMI"),
        'action': 'Tests'
        },
        )


#===============================================================================
# main
#===============================================================================
def main():
    #Get parameters
    parser = argparse.ArgumentParser(description='Request values to Solarmax inverter')
    parser.add_argument('-H', '--host', dest='hostname', action='store', help='Host name', default='192.168.0.123')
    parser.add_argument('-p', '--port', dest='port', type=int, action='store', help='Port value', default='12345')

    parser.add_argument('-d', '--dbname', dest='dbFileName', action='store', help='Database filename', default='Solarmax_data2.s3db')
    parser.add_argument('-a', '--action', dest='action', action='store', help='Action (Send a predefined list of commands)', choices=['Realtime', 'Stats', 'History', 'Info', 'SetTime'], default='Info')

    args = parser.parse_args()
    
    #Connect to inverter
    #Create socket and connect
    try:
        my_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_sock.settimeout(15)
        my_sock.connect((args.hostname, args.port))
        
        logger.info("Connected to %s:%d" % (args.hostname, args.port))

        if args.action == "SetTime":
            logger.info("Action: SetTime")
            #TODO SetTime to current time
            dataConverter = DataConverter()
            setTimeToCurrentTime(my_sock, dataConverter)
        else:
            #Connect to the database
            dbm = DBManager(args.dbFileName)
            if dbm.connectFailure == 1:
                print("Can't connect to database")
                logger.error("Can't connect to database '%s'" % args.dbFileName)
            else:
                dbm.CreateTables(GlobalData.dbTables)
            
            dataConverter = DataConverter(dbm)
            for group in GROUPS_COMMANDS:
                if group["action"] == args.action:
                    logger.info("Request group '%s'" % group["group"])
                    print(GREEN + group["group"] + ENDC)
                    requestAndPrintCommands(my_sock, dataConverter, group["cmds"])
                    print()

            #Commit data to DB
            dataConverter.CommitDataToDb()
            
            #Add last update time in database
            addLastUpdateInDb(dbm, args.action)
            
            #Close database
            dbm.Close()

    except socket.error as e:
        print("Socket error: %s" % e)
        logger.error("Socket error: %s" % e)
    
    #Close the socket
    my_sock.close()
    logger.info("Disconnected")


#===============================================================================
# testCmd
#===============================================================================
def testCmd():
    cmd = Request(["SAL"])
    print(cmd.BuildCommand())
    
    cmd = Request("SAL")
    print(cmd.BuildCommand())

    cmd = Request(["SAL", "SYS"])
    print(cmd.BuildCommand())
    
    cmd = Request(["SDAT"], way=Request.SET, attr=datetime.now(), fFormat=Format.DateTime2Hex)
    print(cmd.BuildCommand())
    

#===============================================================================
# testRsp
#===============================================================================
def testRsp():
    #rsp = Response("{01;FB;23|64:SAL=0;SYS=4E24,0|075F}")
    #rsp = Response("{01;FB;48|64:SDAT=7DC0219,E050;SNM=FF,FF,FF,0;SRD=0;SRS=0;TCP=3039|107D}")
    rsp = Response("{01;FB;3B|64:TNF=138C;UDC=CDD;UGD=766;UL1=92B;UM1=928|0D73}")
    cmdDict = rsp.ParseCommandResponse()
    
    dc = DataConverter()
    for cmd, values in list(cmdDict.items()):
        dc.TreatResponse(cmd, values)

    rsp = Response("{01;FB;38|64:IL1=2D1;PAC=D16;PDC=DD2;PRL=3A;TKK=2C|0CC1}")
    cmdDict = rsp.ParseCommandResponse()
    for cmd, values in list(cmdDict.items()):
        dc.TreatResponse(cmd, values)
    
    dc.GetCurrentValue("TNF")
    dc.GetCurrentValue("UL1")
    dc.GetCurrentValue("IL1")


#===============================================================================
# testInsertLastUpdateInDb
#===============================================================================
def testInsertLastUpdateInDb():
    dbm = DBManager("../data/Solarmax_data2.s3db")
    
    addLastUpdateInDb(dbm, "Realtime")
    addLastUpdateInDb(dbm, "Stats")


if __name__ == "__main__":
    main()
