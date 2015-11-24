#!/usr/bin/env python
#-*-coding: utf-8 -*-

'''
Usage : python Solarmax.py

Se connecte à l'onduleur et enregistre les données dans la base SQLite.

v1.0 : 2011/12/11
    - Ajout de couleurs sur la sortie 
    - Nettoyage des commandes inutiles
    - Ajouts des commandes EC10 à EC19

Roadmap:
v1.1 : TODO
    - Options pour afficher que les infos dans la console, ou que stocker les valeurs en base
    - Vérifier l'heure
    
v1.2 : TODO
    - Grouper les données affichées dans la console (date heure, stats production, ...)
    - Analyser les erreurs
    - Vérifier les stats par mois avec les stats production en fonction du mois en cours
    - Remise à l'heure ???


Informations et code source Perl ayant servi au développement proviennent
du site http://blog.dest-unreach.be/2009/04/15/solarmax-maxtalk-protocol-reverse-engineered  
'''

import os, sys, re, binascii, socket
from time import *

from SqliteDBManager import *

from datetime import *

#Output colors
RED = '\033[91m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
BLUE = '\033[94m'
ENDC = '\033[0m'

class SolarmaxDataConvertor:
    """Class used to convert data reading from Solarmax to text or mysql resquest"""

    #List of mysql insert requests
    m_sqlRequestList = []
    
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
        20134:"Ventilateur défectueux"}

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

    def convertGeneric(self, value):
        return value

    def convertX1(self, value):
        return str(int(value, 16))
        
    def convertX10(self, value):
        return str(int(value, 16)*10)
            
    def convertX100(self, value):
        return str(int(value, 16)*100)

    def convertX500(self, value):
        return str(int(value, 16)*500)

    def convertD2(self, value):
        return str(int(value, 16)/2.0)

    def convertD10(self, value):
        return str(int(value, 16)/10.0)
        
    def convertD100(self, value):
        return str(int(value, 16)/100.0)
        
    def convertDate(self, value):
        #7DB0206 -> 2011-02-06
        m = re.split("(.+)(.{2})(.{2})", value)
        
        #print "Date ", repr(m)
        year = str(int(m[1], 16))
        month = str(int(m[2], 16))
        day = str(int(m[3], 16))
        
        return year + "-" + month + "-" + day
        
    def convertTime(self, value):
        return strftime('%H:%M:%S', gmtime(int(value,16)))
        
    def convertDateEnergy(self, args):
        #7DB0112,1B,11F6,51 -> date, total watt, peak watt, hours sunshine
        vals = args.split(',')
        
        date = self.convertDate(vals[0])
        total = self.convertD10(vals[1])
        peak = self.convertD2(vals[2])
        hours = self.convertD10(vals[3])
        
        return date + " : " + total + " kWh, " + peak + " W peak, " + hours + " hours"
        
    def convertSYS(self, args):
        #TODO : handle unknown status
        code = args.split(',')[0]
        return self.m_Status[int(code, 16)]
        
    def convertError(self, args):
        vals = args.split(',')
        
        date = self.convertDate(vals[0])
        time = self.convertTime(vals[1])
        
        key = int(vals[2], 16)
        if self.m_Status.has_key(key):
            error = self.m_Status[key]
        else:
            error = "Unknown error (%s)" % key
        
        return date + " " + time + " : " + error 

    def convertType(self, value):
        #TODO : handle unknown model
        return self.m_DeviceType[int(value,16)]

    def outputConsole(self, description, convert, value):
        print description, convert(self, value)
    
    def outputDBEnergyDay(self, description, convert, value):
        #7DB0112,1B,11F6,51 -> date, total watt, peak watt, hours sunshine
        vals = value.split(',')
        
        #date = convertDate(vals[0])
        m = re.split("(.+)(.{2})(.{2})", vals[0])
        year = "%04d" % int(m[1], 16)
        month = "%02d" % int(m[2], 16)
        day = "%02d" % int(m[3], 16)
        
        date = year + "/" + month + "/" + day
        
        energy = self.convertD10(vals[1])
        peak = self.convertD2(vals[2])
        hours = self.convertD10(vals[3])
        
        #Build request
        sqlRequest = 'REPLACE INTO EnergyByDay '
        sqlRequest += '(date, year, month, day, energy, peak, hours) '
        sqlRequest += 'VALUES ("%s", "%s", "%s", "%s", "%s", "%s", "%s")' % (date, year, month, day, energy, peak, hours)
        
        self.m_sqlRequestList.append(sqlRequest)

        
    def outputDBEnergyMonth(self, description, convert, value):
        #7DB0112,1B,11F6,51 -> date, total watt, peak watt, hours sunshine
        vals = value.split(',')
        
        #date = convertDate(vals[0])
        m = re.split("(.+)(.{2})(.{2})", vals[0])
        year = "%04d" % int(m[1], 16)
        month = "%02d" % int(m[2], 16)
        day = "01"
        
        date = year + "/" + month + "/" + day
        
        energy = self.convertD10(vals[1])
        peak = self.convertD2(vals[2])
        hours = self.convertD10(vals[3])
        
        #Build request
        sqlRequest = 'REPLACE INTO EnergyByMonth '
        sqlRequest += '(date, year, month, energy, peak, hours) '
        sqlRequest += 'VALUES ("%s", "%s", "%s", "%s", "%s", "%s")' % (date, year, month, energy, peak, hours)
        
        self.m_sqlRequestList.append(sqlRequest)
        
        #Just for console info
        print "%s : %s kWh" % (date, energy)
        
        
    def outputDBEnergyYear(self, description, convert, value):
        #7DB0112,1B,11F6,51 -> date, total watt, peak watt, hours sunshine
        vals = value.split(',')
        
        #date = convertDate(vals[0])
        m = re.split("(.+)(.{2})(.{2})", vals[0])
        year = "%04d" % int(m[1], 16)
        month = "01"
        day = "01"
        
        date = year + "/" + month + "/" + day
        
        energy = self.convertD10(vals[1])
        peak = self.convertD2(vals[2])
        hours = self.convertD10(vals[3])
        
        if year != "2000":
            #Build request
            sqlRequest = 'REPLACE INTO EnergyByYear '
            sqlRequest += '(date, year, energy, peak, hours) '
            sqlRequest += 'VALUES ("%s", "%s", "%s", "%s", "%s")' % (date, year, energy, peak, hours)
            
            self.m_sqlRequestList.append(sqlRequest)


    m_cmdArray = [
        {"Convert":convertX1, "Name":"ADR", "Descr":"Address", "Output":outputConsole},
        {"Convert":convertType, "Name":"TYP", "Descr":"Type", "Output":outputConsole},
        {"Convert":convertD10, "Name":"SWV", "Descr":"Software version", "Output":outputConsole},
        {"Convert":convertX1, "Name":"DDY", "Descr":"Date day", "Output":outputConsole},
        {"Convert":convertX1, "Name":"DMT", "Descr":"Date month", "Output":outputConsole},
        {"Convert":convertX1, "Name":"DYR", "Descr":"Date year", "Output":outputConsole},
        {"Convert":convertX1, "Name":"THR", "Descr":"Time hours", "Output":outputConsole},
        {"Convert":convertX1, "Name":"TMI", "Descr":"Time minutes", "Output":outputConsole},

        #Not in Solarmax 3000S
        #{"Convert":convertGeneric, "Name":"E11", "Descr":"???Error 1, number???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E1D", "Descr":"???Error 1, day???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E1M", "Descr":"???Error 1, month???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E1h", "Descr":"???Error 1, hour???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E1m", "Descr":"???Error 1, minute???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E21", "Descr":"???Error 2, number???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E2D", "Descr":"???Error 2, day???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E2M", "Descr":"???Error 2, month???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E2h", "Descr":"???Error 2, hour???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E2m", "Descr":"???Error 2, minute???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E31", "Descr":"???Error 3, number???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E3D", "Descr":"???Error 3, day???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E3M", "Descr":"???Error 3, month???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E3h", "Descr":"???Error 3, hour???", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"E3m", "Descr":"???Error 3, minute???", "Output":outputConsole},

        {"Convert":convertX1, "Name":"KHR", "Descr":"Operating hours", "Output":outputConsole},
        {"Convert":convertX100, "Name":"KDY", "Descr":"Energy today [Wh]", "Output":outputConsole},
        {"Convert":convertX100, "Name":"KLD", "Descr":"Energy yesterday [Wh]", "Output":outputConsole},
        {"Convert":convertX1, "Name":"KMT", "Descr":"Energy this month [kWh]", "Output":outputConsole},
        {"Convert":convertX1, "Name":"KLM", "Descr":"Energy last month [kWh]", "Output":outputConsole},
        {"Convert":convertX1, "Name":"KYR", "Descr":"Energy this year [kWh]", "Output":outputConsole},
        {"Convert":convertX1, "Name":"KLY", "Descr":"Energy last year [kWh]", "Output":outputConsole},
        {"Convert":convertX1, "Name":"KT0", "Descr":"Energy total [kWh]", "Output":outputConsole},

        {"Convert":convertGeneric, "Name":"LAN", "Descr":"Language", "Output":outputConsole},

        {"Convert":convertD10, "Name":"UDC", "Descr":"DC voltage [V]", "Output":outputConsole},
        {"Convert":convertD10, "Name":"UL1", "Descr":"AC voltage [V]", "Output":outputConsole},
        {"Convert":convertD100, "Name":"IDC", "Descr":"DC current [A]", "Output":outputConsole},
        {"Convert":convertD100, "Name":"IL1", "Descr":"AC current [A]", "Output":outputConsole},
        {"Convert":convertD2, "Name":"PAC", "Descr":"AC power [W]", "Output":outputConsole},
        {"Convert":convertD2, "Name":"PIN", "Descr":"Power installed [W]", "Output":outputConsole},
        {"Convert":convertX1, "Name":"PRL", "Descr":"AC power [%]", "Output":outputConsole},
        {"Convert":convertX1, "Name":"CAC", "Descr":"Start ups", "Output":outputConsole},
        {"Convert":convertDate, "Name":"FRD", "Descr":"First run date", "Output":outputConsole},
        
        #Not in Solarmax 3000S
        #{"Convert":convertGeneric, "Name":"SCD", "Descr":"?SCD?", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"SE1", "Descr":"?SE1?", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"SE2", "Descr":"?SE2?", "Output":outputConsole},
        #{"Convert":convertGeneric, "Name":"SPR", "Descr":"?SPR?", "Output":outputConsole},
        
        {"Convert":convertX1, "Name":"TKK", "Descr":"Temperature Heat Sink", "Output":outputConsole},
        {"Convert":convertD100, "Name":"TNF", "Descr":"AC Frequency", "Output":outputConsole},
        {"Convert":convertSYS, "Name":"SYS", "Descr":"Operation State : ", "Output":outputConsole},
        {"Convert":convertGeneric, "Name":"BDN", "Descr":"Build number", "Output":outputConsole},

        {"Convert":convertError, "Name":"EC00", "Descr":"Error 00", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC01", "Descr":"Error 01", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC02", "Descr":"Error 02", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC03", "Descr":"Error 03", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC04", "Descr":"Error 04", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC05", "Descr":"Error 05", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC06", "Descr":"Error 06", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC07", "Descr":"Error 07", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC08", "Descr":"Error 08", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC09", "Descr":"Error 09", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC10", "Descr":"Error 10", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC11", "Descr":"Error 11", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC12", "Descr":"Error 12", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC13", "Descr":"Error 13", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC14", "Descr":"Error 14", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC15", "Descr":"Error 15", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC16", "Descr":"Error 16", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC17", "Descr":"Error 17", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC18", "Descr":"Error 18", "Output":outputConsole},
        {"Convert":convertError, "Name":"EC19", "Descr":"Error 19", "Output":outputConsole},

        {"Convert":convertDateEnergy, "Name":"DD00", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD01", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD02", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD03", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD04", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD05", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD06", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD07", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD08", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD09", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD10", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD11", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD12", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD13", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD14", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD15", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD16", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD17", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD18", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD19", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD20", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD21", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD22", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD23", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD24", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD25", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD26", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD27", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD28", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD29", "Descr":"Energy by days", "Output":outputDBEnergyDay},
        {"Convert":convertDateEnergy, "Name":"DD30", "Descr":"Energy by days", "Output":outputDBEnergyDay},

        {"Convert":convertDateEnergy, "Name":"DM00", "Descr":"Energy by months", "Output":outputDBEnergyMonth},
        {"Convert":convertDateEnergy, "Name":"DM01", "Descr":"Energy by months", "Output":outputDBEnergyMonth},
        {"Convert":convertDateEnergy, "Name":"DM02", "Descr":"Energy by months", "Output":outputDBEnergyMonth},
        {"Convert":convertDateEnergy, "Name":"DM03", "Descr":"Energy by months", "Output":outputDBEnergyMonth},
        {"Convert":convertDateEnergy, "Name":"DM04", "Descr":"Energy by months", "Output":outputDBEnergyMonth},
        {"Convert":convertDateEnergy, "Name":"DM05", "Descr":"Energy by months", "Output":outputDBEnergyMonth},
        {"Convert":convertDateEnergy, "Name":"DM06", "Descr":"Energy by months", "Output":outputDBEnergyMonth},
        {"Convert":convertDateEnergy, "Name":"DM07", "Descr":"Energy by months", "Output":outputDBEnergyMonth},
        {"Convert":convertDateEnergy, "Name":"DM08", "Descr":"Energy by months", "Output":outputDBEnergyMonth},
        {"Convert":convertDateEnergy, "Name":"DM09", "Descr":"Energy by months", "Output":outputDBEnergyMonth},
        {"Convert":convertDateEnergy, "Name":"DM10", "Descr":"Energy by months", "Output":outputDBEnergyMonth},
        {"Convert":convertDateEnergy, "Name":"DM11", "Descr":"Energy by months", "Output":outputDBEnergyMonth},

        {"Convert":convertDateEnergy, "Name":"DY00", "Descr":"Energy by years", "Output":outputDBEnergyYear},
        {"Convert":convertDateEnergy, "Name":"DY01", "Descr":"Energy by years", "Output":outputDBEnergyYear},
        {"Convert":convertDateEnergy, "Name":"DY02", "Descr":"Energy by years", "Output":outputDBEnergyYear},
        {"Convert":convertDateEnergy, "Name":"DY03", "Descr":"Energy by years", "Output":outputDBEnergyYear},
        {"Convert":convertDateEnergy, "Name":"DY04", "Descr":"Energy by years", "Output":outputDBEnergyYear},
        {"Convert":convertDateEnergy, "Name":"DY05", "Descr":"Energy by years", "Output":outputDBEnergyYear},
        {"Convert":convertDateEnergy, "Name":"DY06", "Descr":"Energy by years", "Output":outputDBEnergyYear},
        {"Convert":convertDateEnergy, "Name":"DY07", "Descr":"Energy by years", "Output":outputDBEnergyYear},
        {"Convert":convertDateEnergy, "Name":"DY08", "Descr":"Energy by years", "Output":outputDBEnergyYear},
        {"Convert":convertDateEnergy, "Name":"DY09", "Descr":"Energy by years", "Output":outputDBEnergyYear},
    ]
    
    def parseResponse(self, response):
        parts = response.split("|")

        #header = parts[0] 
        body = parts[1]
        #checksum = parts[2]
        
        if not body: 
            print (YELLOW + "No response : %s" + ENDC) % response
            return
        
        #port = body.split(':')[0]
        data = body.split(':')[1]
        
        #separate each command response
        cmdList = data.split(';')
        
        #Treat each commande response
        for cmd in cmdList:
            self.treatValue(cmd)


    def treatValue(self, cmd):
        key = cmd.split('=')[0]
        value = cmd.split('=')[1]
        
        #print [k for k in m_cmdArray if k["Name"] == key]
        bFound = False
        for k in self.m_cmdArray:
            if k["Name"] == key:
                #print k["Descr"], k["Convert"](value)
                bFound = True
                k["Output"](self, k["Descr"], k["Convert"], value)
                
        if bFound == False:
            print (RED+"Command not found : %s = %s"+ENDC) % (key, value)


    def checksum16(self, sText):
        '''Calculate the chekcum 16 of the given argument'''
        #Convert string to char array
        cArray = list(sText)
        sum = 0
        for c in cArray:
            sum += ord(c)
            sum %= 2**16
        
        return sum
        
    def makeMsg(self, sBody):
        srcAddr = "FB"
        destAddr = "01"
        #destAddr = "65"
        
        totalLen = len("{00;00;00||0000}") + len(sBody)
        
        msg = "%s;%s;%02X|%s|" % (srcAddr, destAddr, totalLen, sBody)
        checksum = self.checksum16(msg)
        
        return "{%s%04X}" % (msg, checksum)


m_cmdAll= (
        #Infos software
        {'group':'Infos software', 'cmds':(
        "ADR", "TYP", "SWV", "LAN", 
        "CAC", 
        "FRD", 
        "BDN",)
        },

        #Date and Time
        {'group':'Date and Time', 'cmds':(
        "DDY", "DMT", "DYR", "THR", "TMI",)
        },

        #Stats Production
        {'group':'Stats Production', 'cmds':(
        "KHR", "KDY", "KLD", "KMT", "KLM", "KYR", "KLY", "KT0",)
        },

        #Current values
        {'group':'Current values', 'cmds':(
        "UDC", "UL1", 
        "IDC", "IL1", 
        "PAC", "PIN", "PRL", 
        "TNF", 

        "TKK", 
        "SYS", )
        },
 
        #Errors
        {'group':'Errors', 'cmds':(
        "EC00", "EC01", "EC02", "EC03", "EC04", "EC05", "EC06", "EC07", "EC08", "EC09",
        "EC10", "EC11", "EC12", "EC13", "EC14", "EC15", "EC16", "EC17", "EC18", "EC19",)
        },

        #Stats by day
        {'group':'Stats by day', 'cmds':(
        "DD00", "DD01", "DD02", "DD03", "DD04", "DD05", "DD06", "DD07", "DD08", "DD09",
        "DD10", "DD11", "DD12", "DD13", "DD14", "DD15", "DD16", "DD17", "DD18", "DD19",
        "DD20", "DD21", "DD22", "DD23", "DD24", "DD25", "DD26", "DD27", "DD28", "DD29",
        "DD30",)
        },

        #Stats by month
        {'group':'Stats by month', 'cmds':(
        "DM00", "DM01", "DM02", "DM03", "DM04", "DM05", "DM06", "DM07", "DM08", "DM09", "DM10", "DM11",)
        },

        #Stats by year
        {'group':'Stats by year', 'cmds':(
        "DY00", "DY01", "DY02", "DY03", "DY04", "DY05", "DY06", "DY07", "DY08", "DY09",)
        },
        
        #Tests
        {'group':'Tests', 'cmds':(
        "DDY", "DMT", "DYR", "THR", "TMI")
        },
        )

def cmd_setTimeToNow():
    
    now = datetime.now()
    #print 'Setting date and time to %s' % now
    seconds = now.hour * 3600 + now.minute * 60 + now.second
    hex_datetime = '%03X%02X%02X,%04X' % (now.year, now.month, now.day, seconds)
    
    cmd = "C8:SDAT=%s" % hex_datetime
    
    return cmd

def main(argv):
    #HOST = '127.0.0.1'    # The remote host
    HOST = '192.168.0.123'
    PORT = 12345

    #Create Dataconvertor object
    inverter = SolarmaxDataConvertor()
    
    #Create socket and connect
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    
    #TODO : manage connection errors
    print "Connected\n"
    
    #Send all commands
    cmdToRequest = m_cmdAll
    
    for item in cmdToRequest:
        group = item['group']
        
        #if(group != 'Tests'): continue
        #if(group != 'Current values'): continue
        
        print
        print GREEN + group + ENDC
        
        
        
        for cmd in item['cmds']:
            s.send(inverter.makeMsg("64:" + cmd))
            data = s.recv(1024)
            #Parse the received data
            inverter.parseResponse(data)
            
            
    #Set date
    #s.send(inverter.makeMsg(cmd_setTimeToNow()))
    #data = s.recv(1024)
    #print repr(data)
    
    #Close the socket
    s.close()
    print "Disconnected\n"

    #Execute Myqsl requests
    print "Will insert data in database file " + GlobalData.dbFileName
    InsertInDatabase(inverter.m_sqlRequestList)
    print "Done"
    
def InsertInDatabase(sqlReqList):
    #Connect to the database
    dbm = DBManager(GlobalData.dbFileName)
    if dbm.connectFailure == 1:
        print "Can't connect to database"
    else:
        dbm.CreateTables(GlobalData.dbTables)
    
    if dbm.connectFailure == 0:
        for req in sqlReqList:
            dbm.ExecuteRequest(req)
            
        dbm.Commit()
    
    dbm.Close()

def ReadOutDataFile(fileName):
    #Create Dataconvertor object
    inverter = SolarmaxDataConvertor()

    #Read the file
    for line in file(fileName).read().split('\n'):
        if line.startswith("'{"):
            inverter.parseResponse(line)
            
    InsertInDatabase(inverter.m_sqlRequestList)

if __name__ == "__main__":
    main(sys.argv[1:])
    #ReadOutDataFile(sys.argv[1])
