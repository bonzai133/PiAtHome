#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 8 déc. 2013

@author: laurent
'''
from bottle import route, template
import json
import datetime

from Charts_Authentication import *


# route to historic
@route("/prod_historic", apply=authenticated)
def prod_historic(db):
    #Month names
    MONTHES_SHORT_NAME = ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Jui', 'Jul', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec']
    MONTHES_LONG_NAME = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

    #Get current month
    currentMonth = datetime.datetime.now().month
    
    #Get years available in stats
    c = db.execute('SELECT distinct year FROM EnergyByMonth ORDER BY year DESC')
    
    availYears = []
    for row in c:
        availYears.append(row[0])

    #Render template
    t = template("historic", title="Pi@Home", login=getLogin(), monthesLong=MONTHES_LONG_NAME, monthesShort=MONTHES_SHORT_NAME, years=availYears, currentMonth=currentMonth)
    return t


#===============================================================================
# JSON data functions
#===============================================================================
@route("/energy_by_year.json", apply=authenticated)
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


@route("/energy_by_month.json", apply=authenticated)
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
    
    #Jqplot need None instead of empty list    
    if len(d1) == 0:
        d1 = [None]
    if len(d2) == 0:
        d2 = [None]

    return json.dumps([d1, d2])


@route("/jsondata2", apply=authenticated)
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


@route("/combobox_years_data.json", apply=authenticated)
def combobox_years_data(db):
    c = db.execute('SELECT distinct year FROM EnergyByMonth ORDER BY year DESC')
    
    data = []
    for row in c:
        data.append(row[0])
        
    #print data
    return json.dumps(data)


@route("/real_time_data.json", apply=authenticated)
def real_time_data(db):
    #Get parameters from request
    key = request.query.get('key')

    data = []
    if key == "LastUpdate":
        #TODO : Get this value from database
        data.append(datetime.datetime.now().strftime("%s"))
    else:
        c = db.execute('SELECT value FROM Realtime where key=?', (key, ))
        try:
            for row in c:
                try:
                    data.append(float(row[0]))
                except:
                    data.append(row[0])
        except:
            pass
    
    return json.dumps([data])


@route("/statistics_data.json", apply=authenticated)
def statistics_data(db):
    #Get parameters from request
    key = request.query.get('key')

    c = db.execute('SELECT value FROM Statistics where key=?', (key, ))

    try:
        data = []
        for row in c:
            try:
                data.append(float(row[0]))
            except:
                data.append(row[0])
    except:
        pass
    
    return json.dumps([data])


@route("/list_errors_grid.json", apply=authenticated)
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
