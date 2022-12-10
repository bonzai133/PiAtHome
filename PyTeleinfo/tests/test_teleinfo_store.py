# -*- coding: utf-8 -*-

from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root) + "/pyteleinfo")
print(sys.path)


import unittest
import mock
from mock import MagicMock
import teleinfo_store

#===============================================================================
# Logging
#===============================================================================
import logging
logging.basicConfig(level=logging.INFO)

#===============================================================================
# TestMain
#===============================================================================
class TestMain(unittest.TestCase):
    def test_create(self):
        #Args
        args = MagicMock()
        args.logConfig = None
        args.createTables = True
        args.dbFileName = "PyTeleinfo/tests/output/test_store.s3db"
        args.teleinfoFilePrefix = ""

        teleinfo_store.process(args)

        # TODO: Check that tables are created

    def test_write(self):
        self.test_create()
        #Args
        args = MagicMock()
        args.logConfig = None
        args.createTables = False
        args.dbFileName = "PyTeleinfo/tests/output/test_store.s3db"
        args.teleinfoFilePrefix = "PyTeleinfo/tests/output_061961603414"

        teleinfo_store.process(args)

        # TODO: Check data written in db
        # dateDay	counterId	indexBase	value
        # 2022-10-02	61961603414	421550	0

if __name__ == '__main__':
    unittest.main()
