# -*- coding: utf-8 -*-

#===============================================================================
# Logs
#===============================================================================
import logging
logger = logging.getLogger()


#===============================================================================
# ScreenOutput
#===============================================================================
class ScreenOutput():
    def __init__(self):
        pass
    
    def TreatCommandsResults(self, action, cmdsValues):
        for cmdKey, cmd in cmdsValues.items():
            print cmd
            
        return True
