# -*- coding: utf-8 -*-

import unittest
import mock
from mock import MagicMock

import sys
from pathlib import Path
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))
print(sys.path)

from pysolarmax.Solarmax import process
from pysolarmax.Command import Command

# ===============================================================================
# Logging
# ===============================================================================
import logging
logging.basicConfig(level=logging.INFO)


# ===============================================================================
# TestConnection
# ===============================================================================
class TestMain(unittest.TestCase):
    @mock.patch('pysolarmax.Solarmax.Inverter')
    def test_connect_error(self, inverter):
        # Args
        args = MagicMock()
        # args.action = 'Realtime'
        # args.output = 'Screen'

        # Patch
        instance = inverter.return_value
        instance.connect.return_value = False

        with self.assertRaises(SystemExit) as cm:
            process(args)

        self.assertEqual(cm.exception.code, 1)

    @mock.patch('pysolarmax.Solarmax.Inverter')
    def test_connect_ok(self, inverter):
        # Args
        args = MagicMock()
        args.action = 'Realtime'
        args.output = 'Screen'
        args.dbFileName = 'Solarmax_data2.s3db'
        args.host = '192.168.0.123'
        args.port = '12345'

        # Patch
        instance = inverter.return_value
        instance.connect.return_value = True

        cmdValues = {}
        cmd = Command("UDC", "UDC value", None)
        cmd.Value = "258.3"
        cmdValues.update({cmd.Name: cmd})

        cmd = Command("SYS", "SYS value", None)
        cmd.Value = "Démarrer"
        cmdValues.update({cmd.Name: cmd})

        instance.getValues.return_value = cmdValues

        process(args)

        instance.getValues.assert_called_once_with(['UDC', 'UL1', 'IDC', 'IL1', 'PAC', 'PIN', 'PRL', 'TNF', 'TKK', 'SYS'])


if __name__ == '__main__':
    unittest.main()
