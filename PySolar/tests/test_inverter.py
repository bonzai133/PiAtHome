# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 18:51:48 2015

@author: laurent
"""

import unittest

import sys
from pathlib import Path
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root) + "/pysolarmax")
print(sys.path)

import mock
from mock import MagicMock
from Inverter import Inverter
import socket

# ===============================================================================
# Logging
# ===============================================================================
import logging
logging.basicConfig(level=logging.INFO)


# ===============================================================================
# TestConnection
# ===============================================================================
class TestConnection(unittest.TestCase):
    @mock.patch('Inverter.socket')
    def test_connect_ok(self, sock):
        # Patch
        # sock.return_value = MagicMock()
        # sock.side_effect = Exception("Boom")
        sock_mock = MagicMock()
        sock_mock.recv.return_value = "World"
        sock.socket.return_value = sock_mock

        # Test
        inverter = Inverter("127.0.0.1", 12345)
        res = inverter.connect()

        # Result
        self.assertTrue(sock.socket.called)
        sock_mock.connect.assert_called_once_with(("127.0.0.1", 12345))
        self.assertTrue(res)

        self.assertTrue(inverter.connected)

    @mock.patch('Inverter.socket')
    def test_disconnect_connected_socket(self, sock):
        # Patch
        sock_mock = MagicMock()
        sock.socket.return_value = sock_mock

        # Tests
        inverter = Inverter("127.0.0.1", 12345)
        res = inverter.connect()
        self.assertTrue(res)

        res = inverter.disconnect()
        self.assertTrue(res)

    @mock.patch('Inverter.socket')
    def test_disconnect_not_connected_socket(self, sock):
        # Patch
        sock_mock = MagicMock()
        sock_mock.connect.side_effect = socket.error(10061, "Connection refused")
        sock.socket.return_value = sock_mock

        # Tests
        inverter = Inverter("127.0.0.1", 12345)
        res = inverter.connect()
        self.assertFalse(res)

        res = inverter.disconnect()
        self.assertTrue(res)

    @mock.patch('Inverter.socket')
    def test_connect_error(self, sock):
        # Patch
        sock_mock = MagicMock()
        sock_mock.connect.side_effect = socket.error(10061, "Connection refused")
        sock.socket.return_value = sock_mock

        # Test
        inverter = Inverter("127.0.0.1", 12346)
        res = inverter.connect()

        # Result
        self.assertFalse(res)
        self.assertFalse(inverter.connected)

    @mock.patch('Inverter.socket')
    def test_set_datetime(self, sock):
        # Patch
        sock_mock = MagicMock()
        sock_mock.recv.return_value = b"{01;FB;15|C8:Ok|042C}"
        sock.socket.return_value = sock_mock

        # Test
        inverter = Inverter("127.0.0.1", 12345)
        res = inverter.connect()
        self.assertTrue(inverter.connected)

        res = inverter.setDateTime()

        # Result
        self.assertTrue(res)


if __name__ == '__main__':
    unittest.main()
