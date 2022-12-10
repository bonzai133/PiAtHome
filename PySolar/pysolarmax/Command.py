# -*- coding: utf-8 -*-


# ===============================================================================
# Command class
# ===============================================================================
class Command():
    def __init__(self, Name, Descr, DataConvert):
        self.Name = Name
        self.Descr = Descr
        self.DataConvert = DataConvert
        self.RawValue = None
        self.Value = None

    def __str__(self):
        return "%s (%s) = %s" % (self.Name, self.Descr, self.Value)

    def __repr__(self):
        return "%s (%s) = %s" % (self.Name, self.Descr, self.Value)

    def SetRawValue(self, rawValue):
        self.RawValue = rawValue
        self.Value = self.DataConvert(self.RawValue)
