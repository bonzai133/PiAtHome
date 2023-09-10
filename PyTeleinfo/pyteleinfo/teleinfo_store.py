#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
'''
Created on 3 janv. 2017

@author: laurent
'''
import logging
import logging.config
import argparse
import sqlite3
import glob
import json

#===============================================================================
# Fixed values
#===============================================================================
INSERT_QUERY = "INSERT OR REPLACE INTO TeleinfoByDay (dateDay, counterId, indexBase, value) VALUES (date('now'), ?, ?, ?)"
PREVIOUS_VALUE_QUERY = "SELECT indexBase FROM TeleinfoByDay where counterId=? AND dateDay=date('now', '-1 day')"


#===============================================================================
# DBManager
#===============================================================================
class DBManager:
    """Management of sqlite database"""
    
    def __init__(self, dbFileName):
        "Connect and create the cursor"
        try:
            self.connection = sqlite3.connect(dbFileName)
        except Exception as err:
            logging.error("DB Connect failed: %s" % err)
            self.connectFailure = 1
        else:
            self.cursor = self.connection.cursor()
            self.connectFailure = 0
    
    def ExecuteRequest(self, req, params=None):
        logging.debug("Request: %s ; params: %s" % (req, params or 'None'))
        try:
            if params is not None:
                self.cursor.execute(req, params)
            else:
                self.cursor.execute(req)
        except Exception as err:
            logging.error("Incorrect SQL request '%s' (%s)\n%s" % (req, params or 'None', err))
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
# doCreateTables
# Execute query to create sqlite tables
#===============================================================================
def doCreateTables(db):
    tableName = "TeleinfoByDay"
    
    query = "CREATE TABLE IF NOT EXISTS %s ("
    query += "dateDay TEXT, counterId INTEGER NOT NULL, indexBase INTEGER NOT NULL, value INTEGER, "
    query += "PRIMARY KEY (dateDay, counterId))"

    db.ExecuteRequest(query % tableName)

    
#===============================================================================
# processCreateTables
# Connect to database and create tables
#===============================================================================
def processCreateTables(dbFileName):
    logging.debug("Enter processCreateTables")
    db = DBManager(dbFileName)
    
    if db.connectFailure == 1:
        logging.error("Can't connect to database '%s'" % dbFileName)
    else:
        doCreateTables(db)
        db.Commit()
        db.Close()


#===============================================================================
# processStoreData
# Read teleinfo data, then connect to database and save daily values
#===============================================================================
def processStoreData(dbFileName, teleinfoFilePrefix):
    logging.debug("Enter processStoreData")
    db = DBManager(dbFileName)
    
    if db.connectFailure == 1:
        logging.error("Can't connect to database '%s'" % dbFileName)
    else:
        data = doReadTeleinfo(teleinfoFilePrefix)
        doStoreData(db, data)
        db.Commit()
        db.Close()


#===============================================================================
# doStoreData
# Store teleinfo BASE index in TeleinfoByDay
# data is a dict:
#  - key is ADCO (counter id)
#  - value is a dict of teleinfo keys
#===============================================================================
def doStoreData(db, data):
    for counterId, teleinfo in list(data.items()):
        logging.debug("Process %s" % counterId)

        if 'BASE' in teleinfo:
            index = int(teleinfo['BASE'])
        elif 'EAIT' in teleinfo:
            index = int(teleinfo['EAIT'])
        elif 'BBRHPJB' in teleinfo and \
            'BBRHCJB' in teleinfo and \
            'BBRHPJW' in teleinfo and \
            'BBRHCJW' in teleinfo and \
            'BBRHPJR' in teleinfo and \
            'BBRHCJR' in teleinfo:
        
            index = int(teleinfo['BBRHPJB']) + int(teleinfo['BBRHCJB']) + \
                int(teleinfo['BBRHPJW']) + int(teleinfo['BBRHCJW']) + \
                int(teleinfo['BBRHPJR']) + int(teleinfo['BBRHCJR'])
                
        else:
            logging.error("Base index not found")

        previous = None
        if db.ExecuteRequest(PREVIOUS_VALUE_QUERY, (counterId, )):
            rows = db.cursor.fetchone()
            if rows is not None:
                previous = rows[0]

        if previous is None:
            #No previous data
            previous = index
            
        delta = index - previous
        db.ExecuteRequest(INSERT_QUERY, (counterId, index, delta))


#===============================================================================
# doReadTeleinfo
# Read teleinfo data stored in json files (1 by counter id)
# Return a dict:
#  - key is ADCO or ADSC (counter id)
#  - value is a dict of teleinfo keys
#===============================================================================
def doReadTeleinfo(fileprefix):
    logging.debug("Enter doReadTeleinfo")
    allinfo = {}
    for f in glob.glob(fileprefix + '*'):
        with open(f, 'r') as fp:
            data = json.load(fp)
            if 'ADCO' in data:
                logging.debug("Valid data found (ADCO): %s" % repr(data))
                allinfo[data['ADCO']] = data
            elif 'ADSC' in data:
                logging.debug("Valid data found (ADSC): %s" % repr(data))
                allinfo[data['ADSC']] = data
                
    return allinfo

#===============================================================================
# process(args)
#===============================================================================
def process(args):
    #Use configuration file ?
    if args.logConfig is not None:
        try:
            logging.config.fileConfig(args.logConfig)
        except Exception as e:
            logging.error("Can't read logger configuration: %s" % e)

    logging.debug("Input Args: %s" % repr(args))
    
    if args.createTables:
        processCreateTables(args.dbFileName)
    else:
        processStoreData(args.dbFileName, args.teleinfoFilePrefix)
    
    logging.debug("----- End of treatment")


#===============================================================================
# main
#===============================================================================
def main():
    #Get parameters
    parser = argparse.ArgumentParser(description='Store daily values of Teleinfo into TeleinfoByDay')
    
    parser.add_argument('-d', '--dbname', dest='dbFileName', action='store', help='Database filename', required=True)
    parser.add_argument('-c', '--createTables', dest='createTables', action='store_true', help='Create required tables in database')
    parser.add_argument('-l', '--log-config', dest='logConfig', action='store', help='Log configuration file')
    parser.add_argument('-f', '--teleinfo-file-prefix', dest='teleinfoFilePrefix', action='store', default="/var/run/shm/teleinfo_", help='Teleinfo file path')

    args = parser.parse_args()

    #Create logger with basic config
    logging.basicConfig()

    process(args)
    
    
if __name__ == '__main__':
    main()
