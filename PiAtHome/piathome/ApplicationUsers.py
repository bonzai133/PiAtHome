#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2 déc. 2013

@author: l.petit
'''

from os import urandom
from base64 import b64encode
from hashlib import sha256
import json


class User(object):
    def __init__(self, name, role):
        self.name = name
        self.role = role


class ApplicationUsers(object):
    '''
    ApplicationUsers : handle user management
    '''
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ApplicationUsers, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, userFile):
        self.m_users = {}
        self.m_userFile = userFile
        self.__loadUsers(userFile)

    def __loadUsers(self, userFile):
        try:
            with open(userFile, 'r') as infile:
                self.m_users = json.load(infile)
        except IOError as e:
            #print "loadUsers exception: %s" % e
            #sha256('Passw0rd@dmin').hexdigest()
            self.m_users = {'admin': {'hash': 'bb59ad73aff30cc6c586754579dba0498a3971e8842698288848739d55685b7e',
                                  'salt': 'hOiqfxGTU1cJQoKaBwOv3nz5NgqPhySkhebhnJaibBA=',
                                  'realname': 'ADMINISTRATOR', 'role': 'admin'}}

    def __saveUsers(self, userFile):
        with open(userFile, 'w') as outfile:
            json.dump(self.m_users, outfile)
        
    def createUser(self, name, realname, password, role):
        salt = b64encode(urandom(32))
        digest = sha256(salt + password).hexdigest()
        
        self.m_users[name] = {'hash': digest, 'realname': realname, 'role': role, 'salt': salt}
        
        #Save new user
        self.__saveUsers(self.m_userFile)
        
    def checkUser(self, name, password):
        retUser = None
        if name in self.m_users:
            user = self.m_users[name]
            if sha256(user['salt'] + password).hexdigest() == user['hash']:
                retUser = User(user['realname'], user['role'])
            
        return retUser


if __name__ == "__main__":
    my_users = ApplicationUsers('test.txt')

    #my_users.saveUsers('test.txt')
    print(my_users.m_users)
        
    my_users.createUser('laurent', 'Laurent', 'pipikaka', 'user')
    my_users.createUser('titi', 'Titi', 'tutu', 'user')
    
    print(my_users.m_users)
