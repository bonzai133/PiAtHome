# -*- coding: utf-8 -*-

from .SqliteDBManager import DBManager
from .SqliteDBManager import GlobalData
import time

# ===============================================================================
# Logs
# ===============================================================================
import logging
logger = logging.getLogger()


# ===============================================================================
# DbOutput
# ===============================================================================
class DbOutput:
    OUTPUT_METHODS = [
        ('OutputRealtime',
         ['SYS', 'UDC', 'UL1', 'IDC', 'IL1', 'PAC', 'PIN', 'PRL', 'TKK', 'TNF']),

        ('OutputStatistics',
         ['KHR', 'KDY', 'KLD', 'KMT', 'KLM', 'KYR', 'KLY', 'KT0']),

        ('OutputError',
         ['EC%02d' % index for index in range(0, 20)]),

        ('OutputStatsYear',
         ['DY%02d' % index for index in range(0, 10)]),

        ('OutputStatsMonth',
         ['DM%02d' % index for index in range(0, 12)]),

        ('OutputStatsDay',
         ['DD%02d' % index for index in range(0, 31)]),
    ]

    # ===========================================================================
    # __init__
    # ===========================================================================
    def __init__(self, dbFileName):
        self.m_sqlRequestList = []
        self.dbFileName = dbFileName

    # ===========================================================================
    # OutputRealtime
    # ===========================================================================
    def OutputRealtime(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))

        # Build request
        sqlRequest = 'REPLACE INTO Realtime '
        sqlRequest += '(key, value, desc) '
        sqlRequest += 'VALUES ("%s", "%s", "%s")' % (cmd.Name, cmd.Value, cmd.Descr)

        logger.debug("Request generated: %s" % sqlRequest)

        self.m_sqlRequestList.append(sqlRequest)

    # ===========================================================================
    # OutputStatistics
    # ===========================================================================
    def OutputStatistics(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))

        # Build request
        sqlRequest = 'REPLACE INTO Statistics '
        sqlRequest += '(key, value, desc) '
        sqlRequest += 'VALUES ("%s", "%s", "%s")' % (cmd.Name, cmd.Value, cmd.Descr)

        logger.debug("Request generated: %s" % sqlRequest)

        self.m_sqlRequestList.append(sqlRequest)

    # ===========================================================================
    # OutputError
    # ===========================================================================
    def OutputError(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))

        # Split values
        (date_str, time_str, errCode, desc) = cmd.Value

        # Build request
        sqlRequest = 'REPLACE INTO ErrorsHistory '
        sqlRequest += '(datetime, errCode, desc) '
        sqlRequest += 'VALUES ("%s %s", "%s", "%s")' % (date_str, time_str, errCode, desc)

        logger.debug("Request generated: %s" % sqlRequest)

        self.m_sqlRequestList.append(sqlRequest)

    # ===========================================================================
    # OutputStatsYear
    # ===========================================================================
    def OutputStatsYear(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))
        # Split values
        (date_str, energy, peak, hours) = cmd.Value

        # Format date
        date_array = date_str.split("-")

        year = date_array[0]
        month = "01"
        day = "01"

        date = "%s-%s-%s" % (year, month, day)

        # year 2000 indicate an empty data
        if year != "2000":
            # Build request
            sqlRequest = 'REPLACE INTO EnergyByYear '
            sqlRequest += '(date, year, energy, peak, hours) '
            sqlRequest += 'VALUES ("%s", "%s", "%s", "%s", "%s")' % (date, year, energy, peak, hours)

            logger.debug("Request generated: %s" % sqlRequest)

            self.m_sqlRequestList.append(sqlRequest)

    # ===========================================================================
    # OutputStatsMonth
    # ===========================================================================
    def OutputStatsMonth(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))

        # Split values
        (date_str, energy, peak, hours) = cmd.Value

        # Format date
        date_array = date_str.split("-")

        year = date_array[0]
        month = date_array[1]
        day = "01"

        date = "%s-%s-%s" % (year, month, day)

        # year 2000 indicate an empty data
        if year != "2000":
            # Build request
            sqlRequest = 'REPLACE INTO EnergyByMonth '
            sqlRequest += '(date, year, month, energy, peak, hours) '
            sqlRequest += 'VALUES ("%s", "%s", "%s", "%s", "%s", "%s")' % (date, year, month, energy, peak, hours)

            logger.debug("Request generated: %s" % sqlRequest)

            self.m_sqlRequestList.append(sqlRequest)

    # ===========================================================================
    # OutputStatsDay
    # ===========================================================================
    def OutputStatsDay(self, cmd):
        logger.debug("%s = %s" % (cmd, cmd.Value))

        # Split values
        (date_str, energy, peak, hours) = cmd.Value

        # Format date
        date_array = date_str.split("-")

        year = date_array[0]
        month = date_array[1]
        day = date_array[2]

        # year 2000 indicate an empty data
        if year != "2000":
            # Build request
            sqlRequest = 'REPLACE INTO EnergyByDay '
            sqlRequest += '(date, year, month, day, energy, peak, hours) '
            sqlRequest += 'VALUES ("%s", "%s", "%s", "%s", "%s", "%s", "%s")' % (date_str, year, month, day, energy, peak, hours)

            logger.debug("Request generated: %s" % sqlRequest)

            self.m_sqlRequestList.append(sqlRequest)

    # ===========================================================================
    # _buildRequests
    # ===========================================================================
    def _buildRequests(self, cmdsValues):
        for cmdName, cmd in list(cmdsValues.items()):
            logger.debug('Command %s' % cmdName)
            for (outputMethod, cmdList) in self.OUTPUT_METHODS:
                if cmdName in cmdList:
                    logger.debug('Output to %s' % outputMethod)
                    method = getattr(self, outputMethod)
                    method(cmd)

    # ===========================================================================
    # CommitDataToDb
    # ===========================================================================
    def CommitDataToDb(self, dbm):
        if dbm.connectFailure == 0:
            for req in self.m_sqlRequestList:
                logger.debug("Will execute: %s" % req)
                dbm.ExecuteRequest(req)

            dbm.Commit()

    # ===============================================================================
    # addLastUpdateInDb
    # ===============================================================================
    def addLastUpdateInDb(self, dbm, action):
        table = None
        if dbm.connectFailure == 0:
            if action == "Stats":
                table = "Statistics"
            elif action == "Realtime":
                table = "Realtime"

            key = "LastUpdate"
            value = str(int(time.time()))
            descr = "Last Update"

            if table is not None:
                # Prepare request
                sqlRequest = 'REPLACE INTO %s ' % table
                sqlRequest += '(key, value, desc) '
                sqlRequest += 'VALUES ("%s", "%s", "%s")' % (key, value, descr)

                # Execute request
                logger.debug("Will execute: %s" % sqlRequest)
                dbm.ExecuteRequest(sqlRequest)

                dbm.Commit()

    # ===========================================================================
    # TreatCommandsResults
    # ===========================================================================
    def TreatCommandsResults(self, action, cmdsValues):
        # Open DB
        dbm = DBManager(self.dbFileName)

        if dbm.connectFailure == 1:
            logger.error("Can't connect to database '%s'" % self.dbFileName)
            return False

        # Create tables if not exists
        dbm.CreateTables(GlobalData.dbTables)

        # Add values to request list
        self._buildRequests(cmdsValues)

        # Execute requests and Commit
        self.CommitDataToDb(dbm)

        # Add last update time in database
        self.addLastUpdateInDb(dbm, action)

        # Close database
        dbm.Close()

        # End
        return True
