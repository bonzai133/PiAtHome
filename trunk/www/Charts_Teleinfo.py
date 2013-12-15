#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 8 déc. 2013

@author: laurent
'''
from bottle import route
import json

from Charts_Authentication import *


@route("/teleinfo_counter_id.json", apply=authenticated)
def teleinfo_counterId(db2):
    query = "SELECT distinct(TeleinfoDaily.counterId), counterName from TeleinfoDaily, TeleinfoCounters WHERE TeleinfoDaily.counterId=TeleinfoCounters.counterId"
    c = db2.execute(query)
    d1 = []

    for row in c:
        d1.append((row[0], row[1]))

    return json.dumps(d1)


@route("/teleinfo_set_counter_id.json", apply=authenticated)
def teleinfo_setCounterId(db2):
    if not current_user().has('admin'):
        retVal = "Seul l'administrateur peut exécuter cette commande."
    else:
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
   

@route("/teleinfo_all_data.json", apply=authenticated)
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


@route("/teleinfo_rawdata.json", apply=authenticated)
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


@route("/teleinfo_delta_from_date.json", apply=authenticated)
def teleinfo_delta_from_date(db2):
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
    print dStart, dEnd
    
    #Query db
    if counterId == "-1":
        query1 = "SELECT distinct(counterId) from TeleinfoDaily"
        c1 = db2.execute(query1)
    else:
        c1 = [[counterId]]
        
    d1 = {}
    for row1 in c1:
        query2 = "SELECT date(T1_date) as d1, max_indexBase as i1 FROM \
                (SELECT T1.date as T1_date, max(T1.indexBase) as max_indexBase \
                  FROM TeleinfoDaily as T1 where counterId=? group by date (T1.date)) \
                WHERE d1 = ? OR d1=? ORDER BY d1 ASC"
        
        c2 = db2.execute(query2, (row1[0], dStart, dEnd))
        
        row = c2.fetchall()
        
        delta = 0
        if len(row) != 2:
            print "Can't compare, row number %d != 2" % len(row)
        else:
            index1 = row[0][1]
            index2 = row[1][1]
            delta = index2 - index1
            #print "%s: %d - %d = %d" % (row1[0], index2, index1, delta)
            d1[row1[0]] = (index1, index2, delta)
    
    #print json.dumps(d1)
    return json.dumps(d1)

