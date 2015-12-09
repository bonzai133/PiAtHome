#!/usr/bin/env python
#-*-coding: utf-8 -*-

'''
Usage python Solarmax.py

Display or store information from a Solarmax Inverter

'''

from Inverter import Inverter


def main():
    inverter = Inverter('192.168.0.123', 12345)
    
    inverter.connect()
    
    cmds = ['SYS', 'PRL', 'PAC']
    values = inverter.getValues(cmds)
    
    for cmd in cmds:
        print values[cmd]
    
    inverter.disconnect()
    

if __name__ == "__main__":
    main()
