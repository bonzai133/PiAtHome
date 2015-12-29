# -*- coding: utf-8 -*-

import unittest
from pysolarmax.Format import Format
from datetime import datetime

#===============================================================================
# Logging
#===============================================================================
import logging
logging.basicConfig(level=logging.INFO)


#===============================================================================
# TestConnection
#===============================================================================
class TestFormat(unittest.TestCase):
    def test_format_date(self):
        fdate = Format.DateTime2Hex(datetime(2015, 12, 1, 13, 54, 37, 194000))
        
        self.assertEqual(fdate, '7DF0C01,C39D')


if __name__ == '__main__':
    unittest.main()
