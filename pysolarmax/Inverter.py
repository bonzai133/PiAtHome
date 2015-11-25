# -*- coding: utf-8 -*-

import socket

class Inverter():
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.m_sock = None
    
    def __del__(self):
        self.disconnect()
    
    def connect(self):
        res = True
        try:
            my_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            my_sock.settimeout(15)
            self.m_sock = my_sock
            
            my_sock.connect((self.hostname, self.port))
    
            my_sock.send("Hello")
            rspData = my_sock.recv(255)
        except socket.error, e:
            res = False
        
        return res
    
    def disconnect(self):
        if self.m_sock is not None:
            self.m_sock.close()
            
        return True
    
    def getValues(self):
        pass
    
    def setDateTime(self):
        pass
