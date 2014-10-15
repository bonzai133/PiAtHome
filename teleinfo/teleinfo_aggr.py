#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Created on 12 janv. 2014

@author: laurent
'''
import os
import re
import logging
import logging.config
import argparse
import sqlite3
import datetime

#Logger
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
LOGCONF_PATH = os.path.join(ROOT_PATH, 'logging_teleinfo.conf')

logging.config.fileConfig(LOGCONF_PATH)
logger = logging.getLogger(__name__)


#===============================================================================
# DBManager
#===============================================================================
Teleinfo_aggr_dbTables = {"TeleinfoByDay": [
                        ('id', 'i', "Primary key"),
                        ('date', "t", "Date"),
                        ('counterId', "n", "Counter identifier (serial number)"),
                        ('indexBase', "n", "Base index (Wh)"),
                        ('value', "n", "daily value (diff from previous day)")],
                     }


class DBManager:
    """Management of a MySQL database"""
    
    def __init__(self, dbFileName):
        "Connect and create the cursor"
        try:
            self.connection = sqlite3.connect(dbFileName)
        except Exception, err:
            logging.error("DB Connect failed: %s" % err)
            self.connectFailure = 1
        else:
            self.cursor = self.connection.cursor()
            self.connectFailure = 0
    
    def CreateTables(self, dictTables):
        for table in dictTables.keys():
            req = "CREATE TABLE IF NOT EXISTS %s (" % table
            
            for descr in dictTables[table]:
                fieldName = descr[0]
                fType = descr[1]
                
                if fType == 'n':
                    fieldType = 'INTEGER'
                elif fType == 'i':
                    fieldType = 'INTEGER PRIMARY KEY'
                elif fType == 'r':
                    fieldType = 'REAL'
                elif fType == 'd':
                    fieldType = 'TEXT PRIMARY KEY'
                elif fType == 't':
                    fieldType = 'TEXT'
                else:
                    fieldType = 'BLOB'
                    
                req = req + "%s %s, " % (fieldName, fieldType)
                
            req = req[:-2] + ")"
                
            self.ExecuteRequest(req)
                
    def DeleteTables(self, dictTables):
        for table in dictTables.keys():
            req = "DROP TABLE %s" % table
            self.ExecuteRequest(req)
        self.Commit()
    
    def ExecuteRequest(self, req):
        logger.debug("Request: %s" % req)
        try:
            self.cursor.execute(req)
        except Exception, err:
            logging.error("Incorrect SQL request (%s)\n%s" % (req, err))
            return 0
        else:
            return 1
    
    def GetResult(self):
        return self.cursor.fetchall()
        
    def Commit(self):
        if self.connection:
            self.connection.commit()
                    
    def Close(self):
        if self.connection:
            self.connection.close()


#===============================================================================
# process
#===============================================================================
def process(dbFileName, dateStart, dateEnd, createTables=False):
    db = DBManager(dbFileName)
    
    if db.connectFailure == 1:
        logger.error("Can't connect to database '%s'" % dbFileName)
    else:
        if createTables:
            doCreateTables(db)
            db.Commit()
            
        doAggregation(db, dateStart, dateEnd)
        
        db.Commit()
        db.Close()


def doCreateTables(db):
    #db.DeleteTables(Teleinfo_aggr_dbTables)
    #db.CreateTables(Teleinfo_aggr_dbTables)
    tableName = "TeleinfoByDay"
    
    query = "CREATE TABLE IF NOT EXISTS %s ("
    query += "dateDay TEXT, counterId INTEGER NOT NULL, indexBase INTEGER NOT NULL, value INTEGER, "
    query += "PRIMARY KEY (dateDay, counterId))"

    db.ExecuteRequest(query % tableName)
   
      
#===============================================================================
# doAggregation
#===============================================================================
def doAggregation(db, dateStart, dateEnd):
#insert into TeleinfoDelta (counterId, date, value, ...)

#SELECT T1.counterId, date(T1.date) as d1, max(T1.indexBase) as m1, d2, m2, m2 - max(T1.indexBase) as diff
#FROM TeleinfoDaily as T1, (SELECT T2.counterId as cid2, date(T2.date) as d2, max(T2.indexBase) as m2 FROM TeleinfoDaily as T2 group by date(T2.date), T2.counterId)
#where T1.counterId=cid2 and d1 = date(d2, '-1 day') group by date(T1.date), T1.counterId;
    query_insert = "INSERT OR REPLACE INTO TeleinfoByDay (dateDay, counterId, indexBase, value) "
    query_select1 = "SELECT date(T1.date, '+1 day') as d1, T1.counterId, m2, m2 - max(T1.indexBase) as diff "
    query_from1 = "FROM TeleinfoDaily as T1, "
    query_select2 = "SELECT T2.counterId as cid2, date(T2.date) as d2, max(T2.indexBase) as m2 "
    query_from2 = "FROM TeleinfoDaily as T2 where d2 between '%s' and '%s' group by date(T2.date), T2.counterId "
    query_where = "WHERE T1.counterId=cid2 and d1 between '%s' and '%s' and d1=date(d2) "
    query_groupby = "GROUP BY date(T1.date), T1.counterId"
    
    query = query_insert + query_select1 + query_from1 + \
                "(" + query_select2 + query_from2 + ") " + query_where + query_groupby
    
    db.ExecuteRequest(query % (dateStart, dateEnd, dateStart, dateEnd))
                    

#===============================================================================
# main
#===============================================================================
def main():
    #Get parameters
    parser = argparse.ArgumentParser(description='Aggregate values of TeleinfoDaily into TeleinfoByDay')
    
    parser.add_argument('-s', '--startDate', dest='dateStart', help='Start date', required=False)
    parser.add_argument('-e', '--endDate', dest='dateEnd', help='End date', required=False)
    
    parser.add_argument('-d', '--dbname', dest='dbFileName', action='store',
                        help='Database filename', required=True)
    
    parser.add_argument('-c', '--createTables', dest='createTables', action='store_true',
                        help='Create required tables in database')

    args = parser.parse_args()

    logger.info("Input Args: %s" % repr(args))
    
    #Check date format
    if args.dateStart is not None:
        if not re.match("\d{4}-\d{2}-\d{2}", args.dateStart):
            parser.error("Start date format must be yyyy-MM-dd")
    else:
        args.dateStart = (datetime.date.today() - datetime.timedelta(2)).strftime("%Y-%m-%d")
        
    if args.dateEnd is not None:
        if not re.match("\d{4}-\d{2}-\d{2}", args.dateEnd):
            parser.error("End date format must be yyyy-MM-dd")
    else:
        args.dateEnd = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d")

    logger.debug("Computed Args: %s" % repr(args))
    process(args.dbFileName, args.dateStart, args.dateEnd, args.createTables)
    
    logger.info("----- End of treatment")

if __name__ == '__main__':
    main()
