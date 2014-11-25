#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 18 mars 2013

@author: l.petit
'''
import os
import sys
import argparse

from bottle import default_app, ServerAdapter, run, install, TEMPLATE_PATH
from bottle import route, template, static_file, request, response, redirect, abort
from bottle_sqlite import SQLitePlugin
from beaker.middleware import SessionMiddleware

from ApplicationUsers import ApplicationUsers

from Charts_Authentication import *
from Charts_Solar import *
from Charts_Teleinfo import *

from requestlogger import WSGILogger, ApacheFormatter
from logging.handlers import TimedRotatingFileHandler


#Set file path
#ROOT_PATH = os.path.dirname(__file__)
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

#Define absolute path of templates for bottle
TEMPLATE_PATH.insert(0, os.path.join(ROOT_PATH, "templates"))

#DB_FILE = os.path.join(ROOT_PATH, "Solarmax_data2.s3db")
DB_FILE_SOLAR = os.path.join("/opt/pysolarmax/data", "Solarmax_data2.s3db")
DB_FILE_TELEINFO = os.path.join("/opt/pysolarmax/data", "Teleinfo_data.s3db")
VAR_LOG_ACCESS = os.path.join("/var/log", "access.log")
VAR_LOG_ACCESS_SSL = os.path.join("/var/log", "access_ssl.log")

#SSL Certificate
SSL_CERTIFICATE = os.path.join(ROOT_PATH, "ssl/cacert.pem")
SSL_PRIVATE_KEY = os.path.join(ROOT_PATH, "ssl/privkey.pem")

#Folders
SCRIPTS_ROOT = os.path.join(ROOT_PATH, "scripts")
SCRIPTS_CSS = os.path.join(ROOT_PATH, "css")
SSL_FILES = os.path.join(ROOT_PATH, "ssl")
IMAGES_FILES = os.path.join(ROOT_PATH, "images")

USERSFILE = os.path.join(ROOT_PATH, "users.txt")


#===============================================================================
# TODO List
#===============================================================================
# - Ajouter le meilleur et pire mois à travers les ans ! (+ légende mois/année) : rouge pointillés
# - Ajouter la valeur finale pour le cumul sur le graph
# - Tableau avec ces infos en dessous du graph
#

#===============================================================================
# Routes definitions
#===============================================================================
@route("/")
def default():
    redirect("/prod_realtime")


#===============================================================================
# Authentication
#===============================================================================
@route("/login", method='POST')
def login():
    name = request.forms.UserName
    passwd = request.forms.Password
    
    user = ApplicationUsers(USERSFILE).checkUser(name, passwd)
    if user:
        session = beakerSession()
        session['username'] = user.name
        session['role'] = user.role
        
    redirect("/prod_realtime")


@route("/logout", method='POST')
def logout():
    session = beakerSession()
    session.delete()


@route('/getUser')
def getUser():
    response.content_type = 'application/json; charset=utf-8'
    username = current_user().name()
    return json.dumps({"user": username})


@route("/createUser", method='POST', apply=authenticated)
def createUser():
    if not current_user().has('admin'):
        return "Seul l'administrateur peut exécuter cette commande."
    else:
        name = request.forms.UserName
        realname = request.forms.RealName
        passwd = request.forms.Password
        
        if not name or not passwd:
            return "Error creating user"
        else:
            ApplicationUsers(USERSFILE).createUser(name, realname, passwd, 'user')
        
    return "OK"


#===============================================================================
# Main pages
#===============================================================================
@route("/authentication")
def authentication():
    return template("authentication", title="Pi@Home", login=getLogin(),
                    isAuthentic=current_user().isAuthentic(), isAdmin=current_user().has("admin"))


@route("/prod_realtime")
@authenticated
def prod_realtime():
    return template("realtime", title="Pi@Home", login=getLogin())


@route("/prod_historic")
@authenticated
def prod_historic():
    return template("historic", title="Pi@Home", login=getLogin())


@route("/prod_statistics")
@authenticated
def prod_statistics():
    return template("statistics", title="Pi@Home", login=getLogin())


@route("/prod_errors")
@authenticated
def prod_errors():
    return template("errors", title="Pi@Home", login=getLogin())


@route("/teleinfo")
@authenticated
def teleinfo():
    return template("teleinfo", title="Pi@Home", login=getLogin())


#===============================================================================
# Static files
#===============================================================================
@route('/scripts/<filename:path>')
def send_scripts(filename):
    return static_file(filename, root=SCRIPTS_ROOT)


@route('/css/<filename:path>')
def send_css(filename):
    return static_file(filename, root=SCRIPTS_CSS)


@route('/favicon.png')
def send_favicon():
    return static_file('favicon.png', root=IMAGES_FILES)


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
      'session.data_dir': './.cache',
      'session.auto': True
    }
    
    #Debug mode ?
    if port != 80 and port != 443:
        #Sqlite db file
        mydbfile_solarmax = os.path.join(ROOT_PATH, "Solarmax_data2.s3db")
        mydbfile_teleinfo = os.path.join(ROOT_PATH, "../teleinfo/Teleinfo_data.s3db")
        access_log_file = 'access.log'

        #Run http test server on given port
        myserver = 'wsgiref'
        
    else:
        #Sqlite db file
        mydbfile_solarmax = DB_FILE_SOLAR
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
    
    plugin2 = SQLitePlugin(dbfile=mydbfile_teleinfo, keyword='db2')
    plugin2.name = "sqlite2"
    install(plugin2)
    
    #Run server
    run(app=loggingapp, host='0.0.0.0', port=port, server=myserver)


if __name__ == "__main__":
    #Get parameters
    parser = argparse.ArgumentParser(description='Web server displaying charts for Solarmax and Teleinfo')

    parser.add_argument('-p', '--port', dest='port', type=int, action='store',
                        help='Listening port for the web server', default=8080)

    args = parser.parse_args()

    main(args.port)
