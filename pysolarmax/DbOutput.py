# -*- coding: utf-8 -*-

#===============================================================================
# Logs
#===============================================================================
import logging
logger = logging.getLogger()


#===============================================================================
# DbOutput
#===============================================================================
class DbOutput:
    def __init__(self, dbm=None):
        self.m_sqlRequestList = []
        self.m_dbm = dbm
        
    def OutputPrint(self, cmd):
        print "%s = %s" % (cmd, cmd.Value)

    def OutputRealtime(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))
        print "%s = %s" % (cmd, cmd.Value)
        #Build request
        sqlRequest = 'REPLACE INTO Realtime '
        sqlRequest += '(key, value, desc) '
        sqlRequest += 'VALUES ("%s", "%s", "%s")' % (cmd.Name, cmd.Value, cmd.Descr)

        logger.debug("Request generated: %s" % sqlRequest)

        self.m_sqlRequestList.append(sqlRequest)

    def OutputStatistics(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))
        print "%s = %s" % (cmd, cmd.Value)
        #Build request
        sqlRequest = 'REPLACE INTO Statistics '
        sqlRequest += '(key, value, desc) '
        sqlRequest += 'VALUES ("%s", "%s", "%s")' % (cmd.Name, cmd.Value, cmd.Descr)

        logger.debug("Request generated: %s" % sqlRequest)

        self.m_sqlRequestList.append(sqlRequest)
        
    def OutputError(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))
        print "%s = %s" % (cmd, cmd.Value)

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
            
    def CommitDataToDb(self):
        if self.m_dbm.connectFailure == 0:
            for req in self.m_sqlRequestList:
                logger.debug("Will execute: %s" % req)
                self.m_dbm.ExecuteRequest(req)
            
            self.m_dbm.Commit()