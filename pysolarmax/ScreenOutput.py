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
    
    def TreatCommandsResults(self, cmdsValues):
        for cmdKey, cmd in cmdsValues.items():
            print cmd
