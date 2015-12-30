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


@route("/teleinfo_values_byday.json", apply=authenticated)
def teleinfo_values_byday(db2):
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
    data_value = []
    #data_index = []
    series_label = []
    
    if counterId == "-1":
        query1 = "SELECT distinct(counterId) from TeleinfoByday"
        c1 = db2.execute(query1)
    else:
        c1 = [[counterId]]
        
    for row1 in c1:
        query2 = "SELECT dateDay, counterId, indexBase, value FROM TeleinfoByday where dateDay between ? and ? and counterId = ?"
        
        c2 = db2.execute(query2, (dStart, dEnd, row1[0]))
        d1 = []
        #d2 = []
        for row in c2:
            d1.append((row[0], row[3]))
            #d2.append((row[0], row[2]))
        
        series_label.append(str(row1[0]))
        data_value.append(d1)
        #data_index.append(d2)
    
    return json.dumps([series_label, data_value])


@route("/teleinfo_index_byday.json", apply=authenticated)
def teleinfo_index_byday(db2):
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
    data_index = []
    series_label = []
    
    if counterId == "-1":
        query1 = "SELECT distinct(counterId) from TeleinfoByday"
        c1 = db2.execute(query1)
    else:
        c1 = [[counterId]]
        
    for row1 in c1:
        query2 = "SELECT dateDay, counterId, indexBase, value FROM TeleinfoByday where dateDay between ? and ? and counterId = ? ORDER BY dateDay ASC"
        
        c2 = db2.execute(query2, (dStart, dEnd, row1[0]))
        
        offset = 0
        d2 = []
        for row in c2:
            if counterId == "-1" and offset == 0:
                offset = row[2]

            d2.append((row[0], row[2] - offset))
        
        series_label.append(str(row1[0]))
        data_index.append(d2)
    
    return json.dumps([series_label, data_index])


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
    #print dStart, dEnd
    
    #Query db
    if counterId == "-1":
        query1 = "SELECT distinct(counterId) from TeleinfoByDay"
        c1 = db2.execute(query1)
    else:
        c1 = [[counterId]]
        
    d1 = {}
    for row1 in c1:
        query2 = "SELECT dateDay, indexBase FROM TeleinfoByDay WHERE (dateDay=? OR dateDay=?) AND counterId=? ORDER BY dateDay ASC"

        c2 = db2.execute(query2, (dStart, dEnd, row1[0]))
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
