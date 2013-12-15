#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 8 déc. 2013

@author: laurent
'''
from bottle import request, redirect


def beakerSession():
    return request.environ.get('beaker.session')


def getLogin():
    if current_user().isAuthentic():
        username = current_user().name()
    else:
        username = "S'identifier"
        
    return username


class current_user():
    def __init__(self):
        self.m_session = beakerSession()
    
    def name(self):
        username = self.m_session.get('username', "")
        return username
    
    def isAuthentic(self):
        username = self.m_session.get('username', None)
        if username is None:
            return False
        
        return True
    
    def has(self, role):
        user_role = self.m_session.get('role', None)
        
        if user_role is not None and role in user_role:
            return True

        return False


def authenticated(func):
    def wrapped(*args, **kwargs):
        if current_user().isAuthentic():
            return func(*args, **kwargs)
        else:
            redirect('/authentication')
    return wrapped


def authorize(role):
    def wrapper(func):
        def authorize_and_call(*args, **kwargs):
            if not current_user().has(role):
                raise Exception('Unauthorized Access!')
            return func(*args, **kwargs)
        return authorize_and_call
    return wrapper

