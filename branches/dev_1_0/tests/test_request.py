# -*- coding: utf-8 -*-

import unittest
from pysolarmax.Request import Request
from pysolarmax.Request import RequestException
from pysolarmax.Format import Format
from pysolarmax.MessageData import MessageData
from datetime import datetime

#===============================================================================
# Logging
#===============================================================================
import logging
logging.basicConfig(level=logging.INFO)


#===============================================================================
# TestConnection
#===============================================================================
class TestRequest(unittest.TestCase):
    def test_get_cmd(self):
        req = Request("SYS")
        reqStr = req.buildRequest()
        
        self.assertEqual(reqStr, '{FB;01;16|64:SYS|0461}')

    def test_get_cmdlist(self):
        req = Request(["ADR", "TYP", "SWV", "LAN"])
        reqStr = req.buildRequest()
        
        self.assertEqual(reqStr, '{FB;01;22|64:ADR;TYP;SWV;LAN|07BF}')

    def test_set_date(self):
        req = Request("SDAT", action=MessageData.SET, attr=datetime(2015, 12, 1, 13, 54, 37, 194000), fFormat=Format.DateTime2Hex)
        reqStr = req.buildRequest()
        
        self.assertEqual(reqStr, '{FB;01;24|C8:SDAT=7DF0C01,C39D|078F}')

    def test_set_missing_attrs(self):
        req = Request("SYS", action=MessageData.SET)
        with self.assertRaises(RequestException):
            reqStr = req.buildRequest()

    def test_set_multiple_cmd(self):
        req = Request(["SDAT", "SBBB"], action=MessageData.SET, attr=datetime(2015, 12, 1, 13, 54, 37, 194000), fFormat=Format.DateTime2Hex)
        
        with self.assertRaises(RequestException):
            reqStr = req.buildRequest()


if __name__ == '__main__':
    unittest.main()
