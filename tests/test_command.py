# -*- coding: utf-8 -*-

import unittest

from pysolarmax.Command import Command
from pysolarmax.DataConverter import DataConverter


#===============================================================================
# Logging
#===============================================================================
import logging
logging.basicConfig(level=logging.INFO)


#===============================================================================
# TestConnection
#===============================================================================
class TestCommand(unittest.TestCase):
    def test_setValue(self):
        cmd = Command('TST', 'Blabla', DataConverter.convertX1)
        
        cmd.SetRawValue(['ABCD'])
        
        self.assertEqual(cmd.RawValue, ['ABCD'])
        self.assertEqual(cmd.Value, '43981')
