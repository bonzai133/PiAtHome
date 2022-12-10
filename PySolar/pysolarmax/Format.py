# -*- coding: utf-8 -*-

# ===============================================================================
# Format conversion
# ===============================================================================
class Format:
    @staticmethod
    def DateTime2Hex(xTime):
        # now = datetime.now()
        seconds = xTime.hour * 3600 + xTime.minute * 60 + xTime.second
        hex_datetime = '%03X%02X%02X,%04X' % (xTime.year, xTime.month, xTime.day, seconds)
        return hex_datetime
