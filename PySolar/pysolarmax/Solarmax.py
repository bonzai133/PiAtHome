#!/usr/bin/env python
#-*-coding: utf-8 -*-

'''
Usage python Solarmax.py

Display or store information from a Solarmax Inverter

'''

import os
import logging
import logging.config

import argparse
from Inverter import Inverter
from ScreenOutput import ScreenOutput
from DbOutput import DbOutput

#===============================================================================
# Logger
#===============================================================================
try:
    ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
    LOGCONF_PATH = os.path.join(ROOT_PATH, 'logging_pysolarmax.conf')
    
    logging.config.fileConfig(LOGCONF_PATH)
except Exception, e:
    print "Can't read logger configuration: %s" % e
logger = logging.getLogger(__name__)


#===============================================================================
# init_groupCommands
# Initialize the commands lists
#===============================================================================
def init_groupsCommands():
    groups = [
        #Infos software
        {
            'group': 'Infos software',
            'cmds': ["ADR", "TYP", "SWV", "LAN", "CAC", "FRD", "BDN", ],
            'action': 'Info'
        },

        #Date and Time
        {
            'group': 'Date and Time',
            'cmds': ["DDY", "DMT", "DYR", "THR", "TMI", ],
            'action': 'Info'
        },

        #Stats Production
        {
            'group': 'Stats Production',
            'cmds': ["KHR", "KDY", "KLD", "KMT", "KLM", "KYR", "KLY", "KT0", ],
            'action': 'Stats'
        },

        #Current values
        {
            'group': 'Current values',
            'cmds': ["UDC", "UL1", "IDC", "IL1", "PAC", "PIN", "PRL", "TNF", "TKK", "SYS", ],
            'action': 'Realtime'
        },
 
        #Errors
        {
            'group': 'Errors1',
            'cmds': ["EC00", "EC01", "EC02", "EC03", "EC04", "EC05", "EC06", "EC07", "EC08", "EC09", ],
            'action': 'History'
        },
        {
            'group': 'Errors2',
            'cmds': ["EC10", "EC11", "EC12", "EC13", "EC14", "EC15", "EC16", "EC17", "EC18", "EC19", ],
            'action': 'History'
        },

        #Stats by day
        {
            'group': 'Stats by day 1',
            'cmds': ["DD00", "DD01", "DD02", "DD03", "DD04", "DD05", "DD06", "DD07", "DD08", "DD09", "DD10", "DD11", "DD12", "DD13", "DD14", "DD15", ],
            'action': 'History'
        },
        {
            'group': 'Stats by day 2',
            'cmds': ["DD15", "DD16", "DD17", "DD18", "DD19", "DD20", "DD21", "DD22", "DD23", "DD24", "DD25", "DD26", "DD27", "DD28", "DD29", "DD30", ],
            'action': 'History'
        },

        #Stats by month
        {
            'group': 'Stats by month',
            'cmds': ["DM00", "DM01", "DM02", "DM03", "DM04", "DM05", "DM06", "DM07", "DM08", "DM09", "DM10", "DM11", ],
            'action': 'History'
        },

        #Stats by year
        {
            'group': 'Stats by year',
            'cmds': ["DY00", "DY01", "DY02", "DY03", "DY04", "DY05", "DY06", "DY07", "DY08", "DY09", ],
            'action': 'History'
        },
        
        #Tests
        {
            'group': 'Tests',
            'cmds': ["DDY", "DMT", "DYR", "THR", "TMI"],
            'action': 'Tests'
        },
    ]
    
    return groups


def process(args):
    #Connect to inverter
    inverter = Inverter(args.hostname, args.port)
    
    if not inverter.connect():
        logger.error("Can't connect to inverter")
        exit(1)
        
    #Request commands
    if args.action == "SetTime":
        logger.info("Action: SetTime")
        result = inverter.setDateTime()
        logger.info("SetTime result=%s" % str(result))
    else:
        groupsCommands = init_groupsCommands()
        allCmds = []
        allValues = {}
        for group in groupsCommands:
            if group["action"] == args.action:
                logger.info("Request group '%s'" % group["group"])
                
                cmds = group["cmds"]
                values = inverter.getValues(cmds)
                
                allCmds.append(cmds)
                allValues.update(values)
    
        #Do outputs
        if args.output == 'Screen':
            output = ScreenOutput()
        elif args.output == 'Database':
            output = DbOutput()
        else:
            print "No output"
            
        if output is not None:
            output.TreatCommandsResults(args.action, allValues)
    
    #Disconnect
    inverter.disconnect()
    
    
def main():
    #Get parameters
    parser = argparse.ArgumentParser(description='Request values to Solarmax inverter')
    parser.add_argument('-H', '--host', dest='hostname', action='store', help='Host name', default='192.168.0.123')
    parser.add_argument('-p', '--port', dest='port', type=int, action='store', help='Port value', default='12345')

    parser.add_argument('-d', '--dbname', dest='dbFileName', action='store', help='Database filename', default='Solarmax_data2.s3db')
    parser.add_argument('-a', '--action', dest='action', action='store', help='Action (Send a predefined list of commands)', choices=['Realtime', 'Stats', 'History', 'Info', 'SetTime'], default='Info')

    parser.add_argument('-o', '--output', dest='output', action='store', help='Output (Output to screen or to database)', choices=['Screen', 'Database'], default='Screen')

    args = parser.parse_args()
    
    process(args)
    

if __name__ == "__main__":
    main()
