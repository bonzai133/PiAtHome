#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 18 mars 2013

@author: l.petit
'''
import os
import sys
import argparse

os.chdir(os.path.dirname(__file__))

from bottle import default_app, ServerAdapter, run, install, TEMPLATE_PATH
from bottle_sqlite import SQLitePlugin
from beaker.middleware import SessionMiddleware

#Set file path
ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../piathome')
sys.path.append(ROOT_PATH)

#Import main app
import Charts

#Define absolute path of templates for bottle
TEMPLATE_PATH.insert(0, os.path.join(ROOT_PATH, "templates"))

#DB_FILE = os.path.join(ROOT_PATH, "Solarmax_data2.s3db")
DB_FILE_SOLAR = os.path.join("/opt/piathome/data", "Solarmax_data2.s3db")
DB_FILE_TELEINFO = os.path.join("/opt/piathome/data", "Teleinfo_data.s3db")

#===============================================================================
# MAIN
#===============================================================================
#------------------------------------------------------------------------------
# main : start the server
#------------------------------------------------------------------------------
def main():
    #Beaker options
    session_opts = {
      'session.type': 'file',
      'session.cookie_expires': True,
      'session.data_dir': '../data/.cache',
      'session.auto': True
    }
    
    #Sqlite db file
    mydbfile_solarmax = DB_FILE_SOLAR
    mydbfile_teleinfo = DB_FILE_TELEINFO
        
    #Create default bottle application
    app = default_app()
    myapp = SessionMiddleware(app, session_opts)

    #Plugins : SQLitePlugin give a connection in each functions with a db parameter
    install(SQLitePlugin(dbfile=mydbfile_solarmax))
    
    plugin2 = SQLitePlugin(dbfile=mydbfile_teleinfo, keyword='db2')
    plugin2.name = "sqlite2"
    install(plugin2)
    
    #Run server
    return myapp

application = main()

