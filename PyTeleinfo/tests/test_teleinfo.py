# -*- coding: utf-8 -*-
import sys
from pathlib import Path
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))
print(sys.path)

import unittest

from mock import MagicMock
from pyteleinfo import teleinfo
import logging

logging.basicConfig(level=logging.INFO)


class TestMain(unittest.TestCase):
    def test_fake(self):
        # Args
        args = MagicMock()
        args.logFile = None
        args.configFile = None
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
