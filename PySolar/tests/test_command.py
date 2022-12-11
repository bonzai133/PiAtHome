# -*- coding: utf-8 -*-

import unittest

import sys
from pathlib import Path
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))
print(sys.path)

from pysolarmax.Command import Command
from pysolarmax.DataConverter import DataConverter


# ===============================================================================
# Logging
# ===============================================================================
import logging
logging.basicConfig(level=logging.INFO)


# ===============================================================================
# TestConnection
# ===============================================================================
class TestCommand(unittest.TestCase):
    def test_setValue(self):
        cmd = Command('TST', 'Blabla', DataConverter.convertX1)

        cmd.SetRawValue(['ABCD'])

        self.assertEqual(cmd.RawValue, ['ABCD'])
        self.assertEqual(cmd.Value, '43981')


if __name__ == '__main__':
    unittest.main()
