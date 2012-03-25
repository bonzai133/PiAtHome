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
        
        msg = "%(1)s;%(2)s;%(3)02X|%(4)s|" % {"1":srcAddr, "2":destAddr, "3":totalLen, "4":sBody}
        checksum = self.checksum16(msg)
        
        return "{%(1)s%(2)04X}" % {"1":msg, "2":checksum}



m_cmdToRequest = (
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
        #{'group':'Tests', 'cmds':(
        #"SAL")
        #},
        )

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
    for item in m_cmdToRequest:
        group = item['group']
        print
        print GREEN + group + ENDC
        
        for cmd in item['cmds']:
            s.send(inverter.makeMsg("64:" + cmd))
            data = s.recv(1024)
            #Parse the received data
            inverter.parseResponse(data)
    
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

"""
    { 'descr' => 'Address',            'name' => 'ADR', 'convert' => sub { return hex($_[0]); } }, # 0
    { 'descr' => 'Type',            'name' => 'TYP', 'convert' => sub { return "0x" . $_[0]; } }, # 1
    { 'descr' => 'Software version',    'name' => 'SWV', 'convert' => sub { return sprintf("%1.1f", hex($_[0]) / 10 ); } }, # 2
    { 'descr' => 'Date day',        'name' => 'DDY', 'convert' => sub { return hex($_[0]); } }, # 3
    { 'descr' => 'Date month',        'name' => 'DMT', 'convert' => sub { return hex($_[0]); } }, # 4
    { 'descr' => 'Date year',        'name' => 'DYR', 'convert' => sub { return hex($_[0]); } }, # 5
    { 'descr' => 'Time hours',        'name' => 'THR', 'convert' => sub { return hex($_[0]); } }, # 6
    { 'descr' => 'Time minutes',        'name' => 'TMI', 'convert' => sub { return hex($_[0]); } }, # 7
    { 'descr' => '???Error 1, number???',    'name' => 'E11', 'convert' => sub { return hex($_[0]); } }, # 8
    { 'descr' => '???Error 1, day???',    'name' => 'E1D', 'convert' => sub { return hex($_[0]); } }, # 9
    { 'descr' => '???Error 1, month???',    'name' => 'E1M', 'convert' => sub { return hex($_[0]); } }, # 10
    { 'descr' => '???Error 1, hour???',    'name' => 'E1h', 'convert' => sub { return hex($_[0]); } }, # 11
    { 'descr' => '???Error 1, minute???',    'name' => 'E1m', 'convert' => sub { return hex($_[0]); } }, # 12
    { 'descr' => '???Error 2, number???',    'name' => 'E21', 'convert' => sub { return hex($_[0]); } }, # 13
    { 'descr' => '???Error 2, day???',    'name' => 'E2D', 'convert' => sub { return hex($_[0]); } }, # 14
    { 'descr' => '???Error 2, month???',    'name' => 'E2M', 'convert' => sub { return hex($_[0]); } }, # 15
    { 'descr' => '???Error 2, hour???',    'name' => 'E2h', 'convert' => sub { return hex($_[0]); } }, # 16
    { 'descr' => '???Error 2, minute???',    'name' => 'E2m', 'convert' => sub { return hex($_[0]); } }, # 17
    { 'descr' => '???Error 3, number???',    'name' => 'E31', 'convert' => sub { return hex($_[0]); } }, # 18
    { 'descr' => '???Error 3, day???',    'name' => 'E3D', 'convert' => sub { return hex($_[0]); } }, # 19
    { 'descr' => '???Error 3, month???',    'name' => 'E3M', 'convert' => sub { return hex($_[0]); } }, # 20
    { 'descr' => '???Error 3, hour???',    'name' => 'E3h', 'convert' => sub { return hex($_[0]); } }, # 21
    { 'descr' => '???Error 3, minute???',    'name' => 'E3m', 'convert' => sub { return hex($_[0]); } }, # 22
    { 'descr' => 'Operating hours',        'name' => 'KHR', 'convert' => sub { return hex($_[0]); } }, # 23
    { 'descr' => 'Energy today [Wh]',    'name' => 'KDY', 'convert' => sub { return (hex($_[0]) * 100); } }, # 24
    { 'descr' => 'Energy yesterday [Wh]',    'name' => 'KLD', 'convert' => sub { return (hex($_[0]) * 100); } }, # 25
    { 'descr' => 'Energy this month [kWh]',    'name' => 'KMT', 'convert' => sub { return hex($_[0]); } }, # 26
    { 'descr' => 'Energy last monh [kWh]',    'name' => 'KLM', 'convert' => sub { return hex($_[0]); } }, # 27
    { 'descr' => 'Energy this year [kWh]',    'name' => 'KYR', 'convert' => sub { return hex($_[0]); } }, # 28
    { 'descr' => 'Energy last year [kWh]',    'name' => 'KLY', 'convert' => sub { return hex($_[0]); } }, # 29
    { 'descr' => 'Energy total [kWh]',    'name' => 'KT0', 'convert' => sub { return hex($_[0]); } }, # 30
    { 'descr' => 'Language',        'name' => 'LAN', 'convert' => sub { return hex($_[0]); } }, # 31
    { 'descr' => 'DC voltage [mV]',        'name' => 'UDC', 'convert' => sub { return (hex($_[0]) * 100); } }, # 32
    { 'descr' => 'AC voltage [mV]',        'name' => 'UL1', 'convert' => sub { return (hex($_[0]) * 100); } }, # 33
    { 'descr' => 'DC current [mA]',        'name' => 'IDC', 'convert' => sub { return (hex($_[0]) * 10); } }, # 34
    { 'descr' => 'AC current [mA]',        'name' => 'IL1', 'convert' => sub { return (hex($_[0]) * 10); } }, # 35
    { 'descr' => 'AC power [mW]',        'name' => 'PAC', 'convert' => sub { return (hex($_[0]) * 500); } }, # 36
    { 'descr' => 'Power installed [mW]',    'name' => 'PIN', 'convert' => sub { return (hex($_[0]) * 500); } }, # 37
    { 'descr' => 'AC power [%]',        'name' => 'PRL', 'convert' => sub { return hex($_[0]); } }, # 38
    { 'descr' => 'Start ups',        'name' => 'CAC', 'convert' => sub { return hex($_[0]); } }, # 39
    { 'descr' => '???',            'name' => 'FRD', 'convert' => sub { return "0x" . $_[0]; } }, # 40
    { 'descr' => '???',            'name' => 'SCD', 'convert' => sub { return "0x" . $_[0]; } }, # 41
    { 'descr' => '???',            'name' => 'SE1', 'convert' => sub { return "0x" . $_[0]; } }, # 42
    { 'descr' => '???',            'name' => 'SE2', 'convert' => sub { return "0x" . $_[0]; } }, # 43
    { 'descr' => '???',            'name' => 'SPR', 'convert' => sub { return "0x" . $_[0]; } }, # 44
    { 'descr' => 'Temerature Heat Sink',    'name' => 'TKK', 'convert' => sub { return hex($_[0]); } }, # 45
    { 'descr' => 'AC Frequency',        'name' => 'TNF', 'convert' => sub { return (hex($_[0]) / 100); } }, # 46
    { 'descr' => 'Operation State',        'name' => 'SYS', 'convert' => sub { return hex($_[0]); } }, # 47
    { 'descr' => 'Build number',        'name' => 'BDN', 'convert' => sub { return hex($_[0]); } }, # 48
    { 'descr' => 'Error-Code(?) 00',    'name' => 'EC00', 'convert' => sub { return hex($_[0]); } }, # 49
    { 'descr' => 'Error-Code(?) 01',    'name' => 'EC01', 'convert' => sub { return hex($_[0]); } }, # 50
    { 'descr' => 'Error-Code(?) 02',    'name' => 'EC02', 'convert' => sub { return hex($_[0]); } }, # 51
    { 'descr' => 'Error-Code(?) 03',    'name' => 'EC03', 'convert' => sub { return hex($_[0]); } }, # 52
    { 'descr' => 'Error-Code(?) 04',    'name' => 'EC04', 'convert' => sub { return hex($_[0]); } }, # 53
    { 'descr' => 'Error-Code(?) 05',    'name' => 'EC05', 'convert' => sub { return hex($_[0]); } }, # 54
    { 'descr' => 'Error-Code(?) 06',    'name' => 'EC06', 'convert' => sub { return hex($_[0]); } }, # 55
    { 'descr' => 'Error-Code(?) 07',    'name' => 'EC07', 'convert' => sub { return hex($_[0]); } }, # 56
    { 'descr' => 'Error-Code(?) 08',    'name' => 'EC08', 'convert' => sub { return hex($_[0]); } }, # 57
"""

"""
the unit is responding to the next commands
but i don’t hnow what they mean

BU1,BU2,BU3,CSU,ENS,ETH,FAN,FID,FRD,IAM,IEA,IED,IEE,IM1,IM2,
IW1,IW2,IDCP,KFS,KHS,KTS,MDT,PAE,PBC,PDC,PWB,PWF,RCH,RND,SAL,
SDV,SL1,SL2,SL3,SRD,SRS,TB1,TB2,TCP,THR,TI1,TI2,TL1,TL2,TL3,
TMI,TSH,TV0..TV9,UGD,UHA,UHD,UI1,UI2,UI3,UM1,UM2,UM3,URH,URL,
UZK,UDCP
"""

"""
The protocol is structured as follows:
STX Src-Add FS Dest-Add FS Length FRS Port US Data FRS Crc ETX

STX Start of Text; indicates the start of a data packet {
ETX End of Text; indicates the end of a data packet if no further packets associated with
this transmission follow }
FRS Frame Separator; indicates start / end of frame data |
US Union Separator; separator between unions :
FS Field Separator; separator for fields within a union ;
Src-Add Address of the sending device 00 … FF
Dest-Add Address of the target device 00 … FF
Length Length of all characters of the data packet 00 … FF
Crc Sum of the ASCII values of all characters from the address up to and including the
FRS, before the Crc 0000 … FFFF
Port Port number for determining the target or the origin of the user data 0 … FFFF
Data User data, 

The Src-Add field contains the device address of the data packet source. The Dest-Add
field contains the address of the device for which the data packet is intended. There are
several predefined addresses which cannot be assigned to SolarMax devices.
Address (dec) Designation Description
0 Broadcast The Broadcast address can only occur as a destination address. All devices connected to the
bus respond to it. It may only be used for point-point connections.
250 Network master The address of the network master (MaxComm Basic, MaxWeb).
251 Host The address of an alternative network master that is connected in addition to the network
master.1)
252 MaxDisplay Reserved address for large displays with the MaxDisplay interface.
253 reserved -
254 reserved -
255 Uninitialized Default value for non-configured network nodes

The address range of the MaxComm protocol is 0 (0×00) to 255 (0xFF). Each address
may only occur once in the network. For SolarMax devices, addresses between 1 and 249
can be used. In respect of SolarMax devices, the network address is set either via their
display or a DIP switch.

AC output PAC Power
Operating hours KHR
Date year DYR
Date month DMT
Date day DDY
Energy year KYR
Energy month KMT
Energy day KDY
Energy total KT0
Installed capacity PIN
Mains cycle duration TNP
Network address ADR
Relative output PRL
Software version SWV
Solar energy year RYR
Solar energy day RDY
Solar energy total RT0
Solar radiation RAD
Voltage DC UDC
Voltage phase 1 UL1
Voltage phase 2 UL2
Voltage phase 3 UL3
Current DC IDC
Current phase 1 IL1
Current phase 2 IL2
Current phase 3 IL3
Temperature power unit 1 TKK
Temperature power unit 2 TK2
Temperature power unit 3 TK3
Temperature solar cells TSZ
Type Type
Time minute TMI
Time hour THR 

The TYPE key provides a value for identifying the device type associated with a network
node. The following values are currently defined:
Device type TYPE (dec)
SolarMax 2000 E 2001
SolarMax 20C 20
MaxMeteo 10210
SolarMax 3000 E 3001
SolarMax 25C 25
MaxCount 10300
SolarMax 4000 E 4000
SolarMax 30C 30
SolarMax 6000 E 6000
SolarMax 35C 35
SolarMax 2000C 2010
SolarMax 50C 50
SolarMax 3000C 3010
SolarMax 80C 80
SolarMax 4000C 4010
SolarMax 100C 100
SolarMax 4200C 4200
SolarMax 300C 300
SolarMax 6000 C 6010
SolarMax 20S 20100
SolarMax 2000 S 20010
SolarMax 35S 20110
SolarMax 3000 S 20020
SolarMax 4200 S 20030
SolarMax 6000 S 20040
SolarMax 6000C 6010
"""

"""
SYS

* 20001,0 En service
* 20002,0 Rayonnement trop faible
* 20003,0 Démarrer
* 20004,0 Exploitation MPP
* 20005,0 Ventilateur tourne
* 20006,0 Exploitation Puissance max
* 20007,0 Limitation température
* 20008,0 Sur secteur
* 20009,0 Courant DC limité
* 20010,0 Courant AC limité
* 20011,0 Mode test
* 20012,0 Télécommandé
* 20013,0 Retard au démarrage

* 20110,0 Tension cct interm. trop élevée
* 20111,0 Surtension
* 20112,0 Surcharge
* 20114,0 Courant de fuite trop élevé
* 20115,0 Pas de secteur
* 20116,0 Fréq. secteur trop élevée
* 20117,0 Fréq. secteur trop basse
* 20118,0 Fonctionnement en îlot
* 20119,0 Mauvaise qualité du secteur
* 20122,0 Tension secteur trop élevée
* 20123,0 Tension secteur trop basse
* 20124,0 Température trop élevée
* 20125,0 Courant secteur dissym.
* 20126,0 Erreur entrée ext. 1
* 20127,0 Erreur entrée ext. 2
* 20129,0 Sens de rotation incorrect
* 20130,0 Faux type d’appareil
* 20131,0 Commut. général hors
* 20132,0 Diode de surtempérature
* 20134,0 Ventilateur défectueux

SAL Ces codes sont en binaire bit par bit. Si plusieurs bits sont présents, les alarmes se combinent
These codes are binary per bit. If more than one bit is set, alarms combine.

Exemple : SAL=9 (8 + 1) => Alarme externe 1, Rupture fusible de la terre centrale

* 0 = OK
* 1 = Alarme externe 1
* 2 = Erreur d’isolation côté DC
* 4 = Courant fuite de terre top élevé
* 8 = Rupture fusible de la terre centrale
* 16 = Alarme externe 2
* 32 = Limitation température longue
* 64 = Erreur d’alimentation AC
* 128 = Alarme externe 4
* 256 = Ventilateur défectueux
* 512 = Rupture de fusible
* 1024 = Panne du capteur temp.
* 2048 = Alarm 12
* …
* 65536 = Alarm 17
"""

"""
(SM00;SM01;SM02;SM03;SM04;SM05;SM06;SM07;SM08;SM09;SM0A;SM0B;SM0C;SM0D;SM0E;SM0F;MCSY;
SYS)

DD00=7DB0111,3C,2002,30
DM05=7DA0800,1168,2ED6,DD6

The first two values are clear: date (7DB=2011, 01=january, 11=17th) and energy. 

DD00 ansers : date,total watt,piek watt,houres sunshine , all on day base

 try “DD00″ to “DD30″, or “DM00″ to “DM11″, or “DY00″ to “DY09″
"""
