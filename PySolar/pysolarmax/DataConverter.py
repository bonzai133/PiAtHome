# -*- coding: utf-8 -*-

import re
from time import strftime
from time import gmtime
from Command import Command

# ===============================================================================
# Logs
# ===============================================================================
import logging
logger = logging.getLogger()


# ===============================================================================
# DataConverter
# ===============================================================================
class DataConverter:
    def __init__(self):
        self.m_Commands = {
            'SYS': Command('SYS', 'Operation State', self.convertSYS),
            'ADR': Command('ADR', 'Address', self.convertX1),
            'TYP': Command('TYP', 'Type', self.convertType),
            'SWV': Command('SWV', 'Software version', self.convertD10),
            'BDN': Command('BDN', 'Build number', self.convertX1),
            'DDY': Command('DDY', 'Date day', self.convertX1),
            'DMT': Command('DMT', 'Date month', self.convertX1),
            'DYR': Command('DYR', 'Date year', self.convertX1),
            'THR': Command('THR', 'Time hours', self.convertX1),
            'TMI': Command('TMI', 'Time minutes', self.convertX1),

            'KHR': Command('KHR', 'Operating hours', self.convertX1),
            'KDY': Command('KDY', 'Energy today [Wh]', self.convertX100),
            'KLD': Command('KLD', 'Energy yesterday [Wh]', self.convertX100),
            'KMT': Command('KMT', 'Energy this month [kWh]', self.convertX1),
            'KLM': Command('KLM', 'Energy last month [kWh]', self.convertX1),
            'KYR': Command('KYR', 'Energy this year [kWh]', self.convertX1),
            'KLY': Command('KLY', 'Energy last year [kWh]', self.convertX1),
            'KT0': Command('KT0', 'Energy total [kWh]', self.convertX1),

            'UDC': Command('UDC', 'DC voltage [V]', self.convertD10),
            'UL1': Command('UL1', 'AC voltage [V]', self.convertD10),
            'IDC': Command('IDC', 'DC current [A]', self.convertD100),
            'IL1': Command('IL1', 'AC current [A]', self.convertD100),
            'PAC': Command('PAC', 'AC power [W]', self.convertD2),
            'PIN': Command('PIN', 'Power installed [W]', self.convertD2),
            'PRL': Command('PRL', 'AC power [%]', self.convertX1),

            'TKK': Command('TKK', 'Temperature Heat Sink', self.convertX1),
            'TNF': Command('TNF', 'AC Frequency', self.convertD100),

            'LAN': Command('LAN', 'Language', self.convertX1),
            'CAC': Command('CAC', 'Start ups', self.convertX1),
            'FRD': Command('FRD', 'First run date', self.convertDate),

            'EC00': Command('EC00', 'Error 00', self.convertError),
            'EC01': Command('EC01', 'Error 01', self.convertError),
            'EC02': Command('EC02', 'Error 02', self.convertError),
            'EC03': Command('EC03', 'Error 03', self.convertError),
            'EC04': Command('EC04', 'Error 04', self.convertError),
            'EC05': Command('EC05', 'Error 05', self.convertError),
            'EC06': Command('EC06', 'Error 06', self.convertError),
            'EC07': Command('EC07', 'Error 07', self.convertError),
            'EC08': Command('EC08', 'Error 08', self.convertError),
            'EC09': Command('EC09', 'Error 09', self.convertError),
            'EC10': Command('EC10', 'Error 10', self.convertError),
            'EC11': Command('EC11', 'Error 11', self.convertError),
            'EC12': Command('EC12', 'Error 12', self.convertError),
            'EC13': Command('EC13', 'Error 13', self.convertError),
            'EC14': Command('EC14', 'Error 14', self.convertError),
            'EC15': Command('EC15', 'Error 15', self.convertError),
            'EC16': Command('EC16', 'Error 16', self.convertError),
            'EC17': Command('EC17', 'Error 17', self.convertError),
            'EC18': Command('EC18', 'Error 18', self.convertError),
            'EC19': Command('EC19', 'Error 19', self.convertError),

            'DY00': Command('DY00', 'Energy by year', self.convertDateEnergy),
            'DY01': Command('DY01', 'Energy by year', self.convertDateEnergy),
            'DY02': Command('DY02', 'Energy by year', self.convertDateEnergy),
            'DY03': Command('DY03', 'Energy by year', self.convertDateEnergy),
            'DY04': Command('DY04', 'Energy by year', self.convertDateEnergy),
            'DY05': Command('DY05', 'Energy by year', self.convertDateEnergy),
            'DY06': Command('DY06', 'Energy by year', self.convertDateEnergy),
            'DY07': Command('DY07', 'Energy by year', self.convertDateEnergy),
            'DY08': Command('DY08', 'Energy by year', self.convertDateEnergy),
            'DY09': Command('DY09', 'Energy by year', self.convertDateEnergy),

            'DM00': Command('DM00', 'Energy by month', self.convertDateEnergy),
            'DM01': Command('DM01', 'Energy by month', self.convertDateEnergy),
            'DM02': Command('DM02', 'Energy by month', self.convertDateEnergy),
            'DM03': Command('DM03', 'Energy by month', self.convertDateEnergy),
            'DM04': Command('DM04', 'Energy by month', self.convertDateEnergy),
            'DM05': Command('DM05', 'Energy by month', self.convertDateEnergy),
            'DM06': Command('DM06', 'Energy by month', self.convertDateEnergy),
            'DM07': Command('DM07', 'Energy by month', self.convertDateEnergy),
            'DM08': Command('DM08', 'Energy by month', self.convertDateEnergy),
            'DM09': Command('DM09', 'Energy by month', self.convertDateEnergy),
            'DM10': Command('DM10', 'Energy by month', self.convertDateEnergy),
            'DM11': Command('DM11', 'Energy by month', self.convertDateEnergy),

            'DD00': Command('DD00', 'Energy by day', self.convertDateEnergy),
            'DD01': Command('DD01', 'Energy by day', self.convertDateEnergy),
            'DD02': Command('DD02', 'Energy by day', self.convertDateEnergy),
            'DD03': Command('DD03', 'Energy by day', self.convertDateEnergy),
            'DD04': Command('DD04', 'Energy by day', self.convertDateEnergy),
            'DD05': Command('DD05', 'Energy by day', self.convertDateEnergy),
            'DD06': Command('DD06', 'Energy by day', self.convertDateEnergy),
            'DD07': Command('DD07', 'Energy by day', self.convertDateEnergy),
            'DD08': Command('DD08', 'Energy by day', self.convertDateEnergy),
            'DD09': Command('DD09', 'Energy by day', self.convertDateEnergy),
            'DD10': Command('DD10', 'Energy by day', self.convertDateEnergy),
            'DD11': Command('DD11', 'Energy by day', self.convertDateEnergy),
            'DD12': Command('DD12', 'Energy by day', self.convertDateEnergy),
            'DD13': Command('DD13', 'Energy by day', self.convertDateEnergy),
            'DD14': Command('DD14', 'Energy by day', self.convertDateEnergy),
            'DD15': Command('DD15', 'Energy by day', self.convertDateEnergy),
            'DD16': Command('DD16', 'Energy by day', self.convertDateEnergy),
            'DD17': Command('DD17', 'Energy by day', self.convertDateEnergy),
            'DD18': Command('DD18', 'Energy by day', self.convertDateEnergy),
            'DD19': Command('DD19', 'Energy by day', self.convertDateEnergy),
            'DD20': Command('DD20', 'Energy by day', self.convertDateEnergy),
            'DD21': Command('DD21', 'Energy by day', self.convertDateEnergy),
            'DD22': Command('DD22', 'Energy by day', self.convertDateEnergy),
            'DD23': Command('DD23', 'Energy by day', self.convertDateEnergy),
            'DD24': Command('DD24', 'Energy by day', self.convertDateEnergy),
            'DD25': Command('DD25', 'Energy by day', self.convertDateEnergy),
            'DD26': Command('DD26', 'Energy by day', self.convertDateEnergy),
            'DD27': Command('DD27', 'Energy by day', self.convertDateEnergy),
            'DD28': Command('DD28', 'Energy by day', self.convertDateEnergy),
            'DD29': Command('DD29', 'Energy by day', self.convertDateEnergy),
            'DD30': Command('DD30', 'Energy by day', self.convertDateEnergy),
        }

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
        20040: "SolarMax 6000 S"
    }

    @staticmethod
    def convertSYS(values):
        code = values[0]
        try:
            retStr = DataConverter.m_Status[int(code, 16)]
        except KeyError:
            logger.warning("Unknown Status (%s)" % int(code, 16))
            retStr = "Unknown Status %d" % int(code, 16)

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
            error = "Unknown error (%s)" % key

        return (date, time, key, error)

    @staticmethod
    def convertType(values):
        value = values[0]
        try:
            retStr = DataConverter.m_DeviceType[int(value, 16)]
        except KeyError:
            logger.warning("Unknown Type %d" % int(value, 16))
            retStr = "Unknown Type %d" % int(value, 16)

        return retStr

    @staticmethod
    def convertDate(values):
        # 7DB0206 -> 2011-02-06
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
        # 7DB0112,1B,11F6,51 -> date, total watt, peak watt, hours sunshine
        date = DataConverter.convertDate([values[0]])
        total = DataConverter.convertD10([values[1]])
        peak = DataConverter.convertD2([values[2]])
        hours = DataConverter.convertD10([values[3]])

        # return date + " : " + total + " kWh, " + peak + " W peak, " + hours + " hours"
        return (date, total, peak, hours)

    # ===========================================================================
    # convertValues
    # commands: dictionary of commands: key=command value=hex_value
    # returns: list of Commands with converted values
    # ===========================================================================
    def convertValues(self, commands):
        convertedCommands = {}
        for command, value in list(commands.items()):
            try:
                cmd = self.m_Commands[command]
                cmd.SetRawValue(value)

                convertedCommands[command] = cmd

                logger.debug("convertValues: %s" % repr(cmd.Value))
            except KeyError:
                logger.error("convertValues: Unknown command '%s' = %s" % (command, value))

        return convertedCommands
