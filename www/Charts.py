#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 18 mars 2013

@author: l.petit
'''
import os
import sys
import json
import datetime
from bottle import default_app, ServerAdapter, run, install, TEMPLATE_PATH
from bottle import route, template, static_file, request, response, redirect, abort
from bottle_sqlite import SQLitePlugin
from beaker.middleware import SessionMiddleware

#Set file path
#ROOT_PATH = os.path.dirname(__file__)
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

#Define absolute path of templates for bottle
TEMPLATE_PATH.insert(0, os.path.join(ROOT_PATH, "templates"))

#DB_FILE = os.path.join(ROOT_PATH, "Solarmax_data2.s3db")
DB_FILE = os.path.join("/opt/pysolarmax", "Solarmax_data2.s3db")

#SSL Certificate
SSL_CERTIFICATE = os.path.join(ROOT_PATH, "ssl/cacert.pem")
SSL_PRIVATE_KEY = os.path.join(ROOT_PATH, "ssl/privkey.pem")

#TEMPLATE_chart = os.path.join(ROOT_PATH, "chart_template")
#TEMPLATE_historic = os.path.join(ROOT_PATH, "historic")
#TEMPLATE_statistics = os.path.join(ROOT_PATH, "statistics")
#TEMPLATE_authentication = os.path.join(ROOT_PATH, "authentication")
SCRIPTS_ROOT = os.path.join(ROOT_PATH, "scripts")
SCRIPTS_CSS = os.path.join(ROOT_PATH, "css")
SSL_FILES = os.path.join(ROOT_PATH, "ssl")




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
    redirect("/prod_historic")


#===============================================================================
# Authentication
#===============================================================================
class AuthException(Exception):
    pass


@route("/login", method='POST')
def login():
    name = request.forms.UserName
    passwd = request.forms.Password
    
    if name == 'titi' and passwd == 'tutu':
        session = beakerSession()
        session['username'] = name
        
    redirect("/prod_historic")


@route("/logout", method='POST')
def logout():
    session = beakerSession()
    session.delete()


@route('/getUser')
def getUser():
    response.content_type = 'application/json; charset=utf-8'
    try:
        username = current_user()
    except:
        username = None
    finally:
        return json.dumps({"user": username})


def beakerSession():
    return request.environ.get('beaker.session')


def current_user():
    session = beakerSession()
    username = session.get('username', None)
    if username is None:
        raise AuthException("Unauthenticated user")
    return username


def authenticated(func):
    def wrapped(*args, **kwargs):
        try:
            user = current_user()
            return func(*args, **kwargs)
        except Exception, e:
            print e
            redirect('/authentication')
    return wrapped


#===============================================================================
# Main pages
#===============================================================================
@route("/authentication")
def authentication():
    return template("authentication", title="Pi@Home")


@route("/prod_realtime")
@authenticated
def prod_realtime():
    return template("realtime", title="Pi@Home")


@route("/prod_historic")
@authenticated
def prod_historic():
    return template("historic", title="Pi@Home")


@route("/prod_statistics")
@authenticated
def prod_statistics():
    return template("statistics", title="Pi@Home")


@route("/prod_errors")
@authenticated
def prod_errors():
    return template("errors", title="Pi@Home")


#===============================================================================
# JSON data functions
#===============================================================================
@route("/energy_by_year.json")
def energy_by_year(db):
    #Get parameters from request
    year1 = request.query.get('year1')
    year2 = request.query.get('year2')
    
    if not year1 or not year2:
        return None

    #Query db
    c = db.execute('SELECT month, energy FROM EnergyByMonth WHERE year = ? ORDER BY month ASC', (year1,))
    d1 = []
    for row in c:
        d1.append((row[0], row[1]))

    c = db.execute('SELECT month, energy FROM EnergyByMonth WHERE year = ? ORDER BY month ASC', (year2,))
    d2 = []
    for row in c:
        d2.append((row[0], row[1]))

    #Cumulate values on each month
    d3 = []
    total = 0
    for tup in d1:
        total += tup[1]
        d3.append((tup[0], total))

    d4 = []
    total = 0
    for tup in d2:
        total += tup[1]
        d4.append((tup[0], total))
            
    #print json.dumps([d1, d2])
    #print json.dumps([d3, d4])
    
    return json.dumps([d1, d2, d3, d4])


@route("/energy_by_month.json")
def energy_by_month(db):
    #Get parameters from request
    year1 = request.query.get('year1')
    year2 = request.query.get('year2')
    month = request.query.get('month')
    
    if not year1 or not year2 or not month:
        print "Missing args"
        return None

    #Query db
    c = db.execute('SELECT day, energy FROM EnergyByDay WHERE year = ? and month = ? ORDER BY day ASC', (year1, month))
    d1 = []
    for row in c:
        d1.append((row[0], row[1]))

    c = db.execute('SELECT day, energy FROM EnergyByDay WHERE year = ? and month = ? ORDER BY day ASC', (year2, month))
    d2 = []
    for row in c:
        d2.append((row[0], row[1]))
    
    return json.dumps([d1, d2])


@route("/jsondata2")
def jsondata2(db):
    #Get parameters from request
    year1 = request.query.get('year1')
    year2 = request.query.get('year2')
    
    if not year1 or not year2:
        return None

    #Query db
    c = db.execute('SELECT month, energy FROM EnergyByMonth WHERE year = ? ORDER BY month ASC', (year1,))
    d1 = []
    for row in c:
        d1.append((row[0], row[1]))

    c = db.execute('SELECT month, energy FROM EnergyByMonth WHERE year = ? ORDER BY month ASC', (year2,))
    d2 = []
    for row in c:
        d2.append((row[0], row[1]))
    
    return json.dumps([d1, d2])


@route("/combobox_years_data.json")
def combobox_years_data(db):
    c = db.execute('SELECT distinct year FROM EnergyByMonth ORDER BY year DESC')
    
    data = []
    for row in c:
        data.append(row[0])
        
    #print data
    return json.dumps(data)


@route("/ticks_monthes.json")
def ticks_monthes():
    data = ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Jui', 'Jul', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec']
    return json.dumps(data)


@route("/ticks_monthes_full.json")
def ticks_monthes_full():
    data = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    return json.dumps(data)


@route("/real_time_data.json")
def real_time_data(db):
    #Get parameters from request
    key = request.query.get('key')

    c = db.execute('SELECT value FROM Realtime where key=?', (key, ))

    try:
        data = []
        for row in c:
            #print row
            try:
                #print "append float"
                data.append(float(row[0]))
            except:
                #print "append str"
                data.append(row[0])
    except:
        #print "in except"
        pass
    
    #print data
    return json.dumps([data])


@route("/statistics_data.json")
def statistics_data(db):
    #Get parameters from request
    key = request.query.get('key')

    c = db.execute('SELECT value FROM Statistics where key=?', (key, ))

    try:
        data = []
        for row in c:
            #print row
            try:
                #print "append float"
                data.append(float(row[0]))
            except:
                #print "append str"
                data.append(row[0])
    except:
        #print "in except"
        pass
    
    #print data
    return json.dumps([data])


@route("/list_errors.json")
def list_errors(db):
    today = datetime.datetime.today()
    delta = datetime.timedelta(7)
    last_days = today - delta
    
    strlastdays = "%04d-%02d-%02d" % (last_days.year, last_days.month, last_days.day)
                  
    c = db.execute('SELECT datetime, errCode, desc \
                    FROM ErrorsHistory \
                    where datetime > ? \
                    ORDER BY datetime ASC', (strlastdays, ))

    data = []
    for row in c:
        data.append({'date': row[0], 'code': row[1], 'desc': row[2]})
        
    if len(data) == 0:
        data.append({'date': strlastdays, 'code': '-----', 'desc': "Pas d'erreur depuis cette date."})

    return json.dumps({"errors": data})


#===============================================================================
# Static files
#===============================================================================
@route('/scripts/<filename:path>')
def send_scripts(filename):
    return static_file(filename, root=SCRIPTS_ROOT)


@route('/css/<filename:path>')
def send_css(filename):
    return static_file(filename, root=SCRIPTS_CSS)


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


class MultiCherryPyServer(ServerAdapter):
    def run(self, handler):
        import cherrypy
        from cherrypy import wsgiserver
        from cherrypy import _cpserver
       
        cherrypy.server.unsubscribe()
       
        #HTTP server
        server1 = wsgiserver.CherryPyWSGIServer((self.host, 80), handler)
        adapter1 = _cpserver.ServerAdapter(cherrypy.engine, server1)
        adapter1.subscribe()
        
        #HTTPS server
        server2 = wsgiserver.CherryPyWSGIServer((self.host, 443), handler)
        server2.ssl_certificate = SSL_CERTIFICATE
        server2.ssl_private_key = SSL_PRIVATE_KEY
        
        adapter2 = _cpserver.ServerAdapter(cherrypy.engine, server2)
        adapter2.subscribe()
       
        #Start all servers
        cherrypy.engine.start()
        #cherrypy.engine.block()

        
def main(debug=False):
    #Beaker options
    session_opts = {
      'session.type': 'file',
      'session.cookie_expires': True,
      'session.data_dir': './.cache',
      'session.auto': True
    }
    
    #Create default bottle application
    app = default_app()
    myapp = SessionMiddleware(app, session_opts)
    
    if debug:
        local_db_file = os.path.join(ROOT_PATH, "Solarmax_data2.s3db")
        
        #Plugins : SQLitePlugin give a connection in each functions with a db parameter
        install(SQLitePlugin(dbfile=local_db_file))
        
        #Run http test server on port 8080
        run(app=myapp, host='127.0.0.1', port="8080")
    else:
        #Plugins : SQLitePlugin give a connection in each functions with a db parameter
        install(SQLitePlugin(dbfile=DB_FILE))

        #Run CherryPy http and https server
        run(app=myapp, host='0.0.0.0', port=443, server=MultiCherryPyServer)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        #Debug mode
        main(True)
    else:
        #Production mode running Cherrypy
        main()
