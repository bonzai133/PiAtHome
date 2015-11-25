# -*- coding: utf-8 -*-

#===============================================================================
# Command class
#===============================================================================
class Command():
    def __init__(self, Name, Descr, DataConvert, Output):
        self.Name = Name
        self.Descr = Descr
        self.DataConvert = DataConvert
        self.Output = Output
        self.Value = None
        
    def __str__(self):
        return "%s : %s" % (self.Name, self.Descr)
