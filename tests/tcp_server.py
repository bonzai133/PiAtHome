# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 21:24:29 2015

@author: laurent
"""

import socket
from multiprocessing import Process

class TcpServer():
    def __init__(self, tcp_port=12345, buffer_size=255):
        self.tcp_port = tcp_port
        self.buffer_size = buffer_size
        self.stop=False
    
    def serveOnceThread(self):
        server = Process(target=self.serveOnce())
        server.start()
        
    def serveOnce(self):
        print "Start"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", self.tcp_port))
        s.listen(1)
        
        conn, addr = s.accept()
        print 'Connection address:', addr
        while 1:
            data = conn.recv(self.buffer_size)
            if not data:
                break
            print "received data:", data
            conn.send("world")  # echo
        conn.close()
        print "End"
    
    def serveForEver(self):
        while self.stop != True:
            self.serveOnce()
        
    def stopServer(self):
        self.stop = True
    
def main():
    server = TcpServer()
    server.serveForEver()

if __name__ == '__main__':
    main()
