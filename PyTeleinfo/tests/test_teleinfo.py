# -*- coding: utf-8 -*-

from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))
print(sys.path)


import unittest
import mock
from mock import MagicMock
from pyteleinfo import teleinfo

#===============================================================================
# Logging
#===============================================================================
import logging
logging.basicConfig(level=logging.INFO)

#===============================================================================
# TestMain
#===============================================================================
class TestMain(unittest.TestCase):
    def test_fake(self):
        #Args
        args = MagicMock()
        args.logFile = None
        args.debug = False
        args.service = False
        args.sleepTime = 2

        args.writeToFile = "PyTeleinfo/tests/output/out_"
        args.consumption = False
        args.production = False
        args.fake = True

        teleinfo.process(args)


if __name__ == '__main__':
    unittest.main()
