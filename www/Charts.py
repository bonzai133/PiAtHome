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
    redirect("/prod_realtime")


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
        
    redirect("/prod_realtime")


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


@route("/teleinfo")
@authenticated
def teleinfo():
    return template("teleinfo", title="Pi@Home")


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


@route("/list_errors_grid.json")
def list_errors_grid(db):
    #Get parameters
    #search = request.query.get('search')
    #nd = request.query.get('nd')
    rows = int(request.query.get('rows'))
    page = int(request.query.get('page'))
    sidx = request.query.get('sidx')
    sord = request.query.get('sord')
    
    #Build request
    today = datetime.datetime.today()
    delta = datetime.timedelta(7)
    last_days = today - delta
    
    strlastdays = "%04d-%02d-%02d" % (last_days.year, last_days.month, last_days.day)
    
    #Calculate limit for pagination
    limit = rows
    offset = rows * (page - 1)
    #print "Limit: %d, %d" % (offset, limit)
    
    #print sidx, sord
    query = 'SELECT datetime, errCode, desc FROM ErrorsHistory where datetime > ? \
                    ORDER BY %s %s LIMIT ?, ?' % (sidx, sord)
                    
    c = db.execute(query, (strlastdays, offset, limit))

    json_data = {
        "page": 0,
        "total": 0,
        "records": 0,
        "rows": []}
    
    data = []
    idx = 1
    for row in c:
        data.append({"id": idx, "cell": [row[0], row[1], row[2]]})
        idx = idx + 1

    #Calculate pagination
    c = db.execute('SELECT count(*) FROM ErrorsHistory where datetime > ? ', (strlastdays, ))
    res = c.fetchall()

    records = res[0][0]
    if records == 0:
        data.append({"id": 1, "cell": [strlastdays, '-----', "Pas d'erreur depuis cette date."]})
        records = 1

    nb_pages = int(records / rows + 1)
    
    #print "page %d/%d, records %d/%d" % (page, nb_pages, rows, records)
    json_data["page"] = page
    json_data["total"] = nb_pages
    json_data["records"] = records
    json_data["rows"] = data
    
    return json.dumps(json_data)


@route("/teleinfo_counter_id.json")
def teleinfo_counterId(db2):
    query = "SELECT distinct(TeleinfoDaily.counterId), counterName from TeleinfoDaily, TeleinfoCounters WHERE TeleinfoDaily.counterId=TeleinfoCounters.counterId"
    c = db2.execute(query)
    d1 = []

    for row in c:
        d1.append((row[0], row[1]))

    return json.dumps(d1)


@route("/teleinfo_set_counter_id.json")
def teleinfo_setCounterId(db2):
    counterId = request.query.get('counterId')
    counterName = request.query.get('counterName')
    
    query_exists = "SELECT EXISTS (SELECT 1 FROM TeleinfoDaily WHERE counterId=?)"
    query = "REPLACE INTO TeleinfoCounters (counterId, counterName) VALUES (?, ?)"
    
    c = db2.execute(query_exists, (counterId, ))
    row = c.fetchone()

    if row and row[0] != 1:
        retVal = "Impossible de changer le nom du compteur n°%s." % (counterId)
    else:
        db2.execute(query, (counterId, counterName))
        db2.commit()
    
        retVal = "Le nom du compteur n°%s a été modifié : '%s'." % (counterId, counterName)
    
    return json.dumps(retVal)
   

@route("/teleinfo_all_data.json")
def teleinfo_all_data(db2):
    #Get parameters from request
    date1 = request.query.get('date1')
    date2 = request.query.get('date2')
    counterId = request.query.get('counterId')
    
    if not date1 or not date2 or not counterId:
        print "Missing args"
        return None

    #Format dates
    dStart = date1.replace('_', '-')
    dEnd = date2.replace('_', '-')
    #print "%s - %s" % (dStart, dEnd)

    #Query db
    data = []
    series_label = []
    
    if counterId == "-1":
        query1 = "SELECT distinct(counterId) from TeleinfoDaily"
        c1 = db2.execute(query1)
    else:
        c1 = [[counterId]]
        
    for row1 in c1:
        query2 = "SELECT \
                date(T1.date) as d1, max(T1.indexBase), d2, m2, m2 - max(T1.indexBase) as diff \
                \
                FROM TeleinfoDaily as T1,\
                  (SELECT date(T2.date) as d2, max(T2.indexBase)  as m2\
                  FROM TeleinfoDaily as T2\
                  WHERE T2.counterId = ?\
                  and d2 between ? and ?\
                  group by date(T2.date))\
                \
                where T1.counterId = ?\
                and d1 between ? and ?\
                and d1 = date(d2, '-1 day')\
                group by date(T1.date)"
        
        c2 = db2.execute(query2, (row1[0], dStart, dEnd, row1[0], dStart, dEnd))
        d1 = []
        d2 = []
        for row in c2:
            d1.append((row[0], row[4]))
            d2.append(row[0])
            #print "%s %s" % (row[0], row[4])
        
        series_label.append(str(row1[0]))
        data.append(d1)
    
    #print json.dumps([series_label, d2, data])
    return json.dumps([series_label, d2, data])


@route("/teleinfo_rawdata.json")
def teleinfo_rawdata(db2):
    #Get parameters from request
    date1 = request.query.get('date1')
    date2 = request.query.get('date2')
    counterId = request.query.get('counterId')
    
    if not date1 or not date2 or not counterId:
        print "Missing args"
        return None

    #Format dates
    dStart = date1.replace('_', '-')
    dEnd = date2.replace('_', '-')

    #Query db
    data = []
    series_label = []
    
    if counterId == "-1":
        query1 = "SELECT distinct(counterId) from TeleinfoDaily"
        c1 = db2.execute(query1)
    else:
        c1 = [[counterId]]
        
    for row1 in c1:
        query2 = "SELECT date, indexBase from TeleinfoDaily where counterId = ? and date between ? and ? order by date asc"

        c2 = db2.execute(query2, (row1[0], dStart, dEnd))
    
        offset = 0
        d1 = []
        d2 = []
        for row in c2:
            if counterId == "-1" and offset == 0:
                offset = row[1]
                
            d1.append((row[0], row[1] - offset))
            d2.append(row[0])
            
        series_label.append(str(row1[0]))
        data.append(d1)
    
    return json.dumps([series_label, d2, data])


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
        local_db_file2 = os.path.join(ROOT_PATH, "../teleinfo/Teleinfo_data.s3db")
       
        #Plugins : SQLitePlugin give a connection in each functions with a db parameter
        install(SQLitePlugin(dbfile=local_db_file))
        
        p2 = SQLitePlugin(dbfile=local_db_file2, keyword='db2')
        p2.name = "sqlite2"
        install(p2)
        
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
