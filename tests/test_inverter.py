# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 18:51:48 2015

@author: laurent
"""

import unittest
import Inverter

class TestConnection(unittest.TestCase):
    def test_connect_ok(self):
        inverter = Inverter("127.0.0.1", 12345)
        res = inverter.connect()
        
        self.assertTrue(res)

    def test_disconnect_ok(self):
        inverter = Inverter("127.0.0.1", 12345)
        res = inverter.connect()
        
        res = inverter.disconnect()
        self.assertTrue(res)

    def test_connect_error(self):
        inverter = Inverter("127.0.0.1", 12346)
        res = inverter.connect()

        self.assertFalse(res)

if __name__ == '__main__':
    unittest.main()
