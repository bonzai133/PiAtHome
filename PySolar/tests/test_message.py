# -*- coding: utf-8 -*-

import unittest

import sys
from pathlib import Path
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))
print(sys.path)

from pysolarmax.MessageData import MessageData
from pysolarmax.MessageData import MessageDataException

# ===============================================================================
# Logging
# ===============================================================================
import logging
logging.basicConfig(level=logging.INFO)


# ===============================================================================
# TestConnection
# ===============================================================================
class TestMessageData(unittest.TestCase):
    def test_parse_message_ok(self):
        msg = MessageData()
        msg.parseMessage('{FB;01;16|64:SYS|0461}')

        self.assertEqual(str(msg), '{FB;01;16|64:SYS|0461}')

    def test_checksum_error(self):
        msg = MessageData()
        with self.assertRaises(MessageDataException):
            msg.parseMessage('{FB;01;16|64:SYS|0462}')

    def test_length_error(self):
        msg = MessageData()
        with self.assertRaises(MessageDataException):
            msg.parseMessage('{FB;01;15|64:SYS|0461}')

    def test_missing_brackets(self):
        msg = MessageData()
        with self.assertRaises(MessageDataException):
            msg.parseMessage('{FB;01;16|64:SYS|0461')
        with self.assertRaises(MessageDataException):
            msg.parseMessage('FB;01;16|64:SYS|0461}')
        with self.assertRaises(MessageDataException):
            msg.parseMessage('FB;01;16|64:SYS|0461')

    def test_split_message_error(self):
        msg = MessageData()
        with self.assertRaises(MessageDataException):
            msg.parseMessage('{FB;01;16|64:SYS}')

    def test_split_header_error(self):
        msg = MessageData()
        with self.assertRaises(MessageDataException):
            msg.parseMessage('{FB;0116|64:SYS|0461}')

    def test_build_message_ok(self):
        msg = MessageData(srcAddr='FB', destAddr='01', payload='SYS')
        self.assertEqual(str(msg), '{FB;01;16|64:SYS|0461}')

        msg = MessageData(srcAddr='FC', destAddr='02', payload='SYS;SAL=0')
        self.assertEqual(str(msg), '{FC;02;1C|64:SYS;SAL=0|05F8}')

    def test_concatenate_message_ok(self):
        msg = MessageData(srcAddr='FB', destAddr='01', payload='SYS')
        msg2 = MessageData(srcAddr='FB', destAddr='01', payload=';SAL=0')

        msg.concatenate(msg2)

        self.assertEqual(str(msg), '{FB;01;1C|64:SYS;SAL=0|05F6}')

    def test_concatenate_addr_mismatch(self):
        msg = MessageData(srcAddr='FB', destAddr='01', payload='SYS')
        msg2 = MessageData(srcAddr='FC', destAddr='01', payload=';SAL=0')
        msg3 = MessageData(srcAddr='FB', destAddr='02', payload=';SAL=0')

        with self.assertRaises(MessageDataException):
            msg.concatenate(msg2)

        with self.assertRaises(MessageDataException):
            msg.concatenate(msg3)

    def test_concatenate_invalid_input(self):
        msg = MessageData(srcAddr='FB', destAddr='01', payload='SYS')

        with self.assertRaises(MessageDataException):
            msg.concatenate('{FB;01;1C|64:SYS;SAL=0|05F6}')

    def test_concatenate_direction_mismatch(self):
        msg = MessageData(srcAddr='FB', destAddr='01', action=MessageData.GET, payload='SYS')
        msg2 = MessageData(srcAddr='FB', destAddr='01', action=MessageData.SET, payload=';SAL=0')

        with self.assertRaises(MessageDataException):
            msg.concatenate(msg2)


if __name__ == '__main__':
    unittest.main()
