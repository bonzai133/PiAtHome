#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse

from bottle import default_app, ServerAdapter, run, install, TEMPLATE_PATH
from bottle_sqlite import SQLitePlugin
from beaker.middleware import SessionMiddleware

from requestlogger import WSGILogger, ApacheFormatter
from logging.handlers import TimedRotatingFileHandler

#Set file path
ROOT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../piathome')
sys.path.append(ROOT_PATH)

#Import main app
import Charts

#Define absolute path of templates for bottle
TEMPLATE_PATH.insert(0, os.path.join(ROOT_PATH, "templates"))

DB_FILE_SOLAR = os.path.join("/opt/pysolarmax/data", "Solarmax_data2.s3db")
DB_FILE_TELEINFO = os.path.join("/opt/pysolarmax/data", "Teleinfo_data.s3db")
DB_FILE_RTSTATS = "/var/run/shm/Solarmax_rtstats.s3db"

VAR_LOG_ACCESS = os.path.join("/var/log", "access.log")
VAR_LOG_ACCESS_SSL = os.path.join("/var/log", "access_ssl.log")

#SSL Certificate
SSL_CERTIFICATE = os.path.join(ROOT_PATH, "ssl/cacert.pem")
SSL_PRIVATE_KEY = os.path.join(ROOT_PATH, "ssl/privkey.pem")


#===============================================================================
# MAIN
#===============================================================================
#Create sub class to handle SSL in cherrypy : require python-cherrypy3
class SSLCherryPyServer(ServerAdapter):
    def run(self, handler):
        from cherrypy import wsgiserver
        server = wsgiserver.CherryPyWSGIServer((self.host, self.port), handler)
        server.ssl_certificate = SSL_CERTIFICATE
        server.ssl_private_key = SSL_PRIVATE_KEY
        try:
            server.start()
        finally:
            server.stop()


#------------------------------------------------------------------------------
# main : start the right server
#------------------------------------------------------------------------------
def main(port):
    #Beaker options
    session_opts = {
        'session.type': 'file',
        'session.cookie_expires': True,
        'session.data_dir': '/var/run/shm/cache_piathome',
        'session.auto': True
    }
    
    #Debug mode ?
    if port != 80 and port != 443:
        #Sqlite db file
        mydbfile_solarmax = os.path.join(ROOT_PATH, "../data/Solarmax_data2.s3db")
        mydbfile_rtstats = os.path.join(ROOT_PATH, "../data/Solarmax_rtstats.s3db")
        mydbfile_teleinfo = os.path.join(ROOT_PATH, "../data/Teleinfo_data.s3db")
        access_log_file = 'access.log'

        #Run http test server on given port
        myserver = 'wsgiref'
        
    else:
        #Sqlite db file
        mydbfile_solarmax = DB_FILE_SOLAR
        mydbfile_rtstats = DB_FILE_RTSTATS
        mydbfile_teleinfo = DB_FILE_TELEINFO
        
        #Run CherryPy http or https server
        if port == 80:
            myserver = 'cherrypy'
            access_log_file = VAR_LOG_ACCESS
        elif port == 443:
            myserver = SSLCherryPyServer
            access_log_file = VAR_LOG_ACCESS_SSL

    #Create default bottle application
    app = default_app()
    myapp = SessionMiddleware(app, session_opts)

    handlers = [TimedRotatingFileHandler(access_log_file, 'd', 7, 90), ]
    loggingapp = WSGILogger(myapp, handlers, ApacheFormatter())
    
    #Plugins : SQLitePlugin give a connection in each functions with a db parameter
    install(SQLitePlugin(dbfile=mydbfile_solarmax))
    
    plugin_teleinfo = SQLitePlugin(dbfile=mydbfile_teleinfo, keyword='db_teleinfo')
    plugin_teleinfo.name = "sqlite_teleinfo"
    install(plugin_teleinfo)

    plugin_rtstats = SQLitePlugin(dbfile=mydbfile_rtstats, keyword='db_rtstats')
    plugin_rtstats.name = "sqlite_rtstats"
    install(plugin_rtstats)
    
    #Run server
    run(app=loggingapp, host='0.0.0.0', port=port, server=myserver, reload=True)


if __name__ == "__main__":
    #Get parameters
    parser = argparse.ArgumentParser(description='Web server displaying charts for Solarmax and Teleinfo')

    parser.add_argument('-p', '--port', dest='port', type=int, action='store',
                        help='Listening port for the web server', default=8080)

    args = parser.parse_args()

    main(args.port)
