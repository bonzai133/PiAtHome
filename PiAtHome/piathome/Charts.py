#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 18 mars 2013

@author: l.petit
'''
import os

from bottle import route, template, static_file, request, response, redirect

from .ApplicationUsers import ApplicationUsers

from .Charts_Authentication import *
from .Charts_Solar import *
from .Charts_Teleinfo import *


#===============================================================================
# TODO List
#===============================================================================
# - Ajouter le meilleur et pire mois à travers les ans ! (+ légende mois/année) : rouge pointillés
# - Ajouter la valeur finale pour le cumul sur le graph
# - Tableau avec ces infos en dessous du graph
#

#===============================================================================
# Config
#===============================================================================
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
USERSFILE = os.path.join(ROOT_PATH, "users.txt")
                         
#Folders
SCRIPTS_ROOT = os.path.join(ROOT_PATH, "scripts")
SCRIPTS_CSS = os.path.join(ROOT_PATH, "css")
SSL_FILES = os.path.join(ROOT_PATH, "ssl")
IMAGES_FILES = os.path.join(ROOT_PATH, "images")


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
