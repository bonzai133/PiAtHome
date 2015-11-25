# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 21:24:29 2015

@author: laurent
"""

import socket

TCP_PORT = 12345
BUFFER_SIZE = 255

def server():
    print "Start"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", TCP_PORT))
    s.listen(1)
    
    conn, addr = s.accept()
    print 'Connection address:', addr
    while 1:
        data = conn.recv(BUFFER_SIZE)
        if not data:
            break
        print "received data:", data
        conn.send("world")  # echo
    conn.close()
    print "End"

def main():
    while 1:
        server()

if __name__ == '__main__':
    main()
