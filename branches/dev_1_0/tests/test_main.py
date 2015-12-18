# -*- coding: utf-8 -*-

import unittest
import mock
from mock import MagicMock
from pysolarmax.Solarmax import process

#===============================================================================
# Logging
#===============================================================================
import logging
logging.basicConfig(level=logging.INFO)


#===============================================================================
# TestConnection
#===============================================================================
class TestMain(unittest.TestCase):
    @mock.patch('pysolarmax.Solarmax.Inverter')
    def test_screen_output(self, inverter):
        #Args
        args = MagicMock()
        args.action = 'Realtime'
        args.output = 'Screen'
        
        #Patch
        inverter.connect.return_value = False
        
        process(args)
        
        self.assertTrue(False)

if __name__ == '__main__':
    unittest.main()
