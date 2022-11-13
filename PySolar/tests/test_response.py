# -*- coding: utf-8 -*-

import unittest

from pysolarmax.Response import Response
from pysolarmax.MessageData import MessageDataException


#===============================================================================
# Logging
#===============================================================================
import logging
logging.basicConfig(level=logging.INFO)


#===============================================================================
# TestConnection
#===============================================================================
class TestResponse(unittest.TestCase):
    def test_length_error(self):
        with self.assertRaises(MessageDataException):
            rsp = Response("{01;FB;28|64:SDAT=7DD}")
        
    def test_checksum_error(self):
        with self.assertRaises(MessageDataException):
            rsp = Response("{01;FB;27|64:SDAT=7DD}")
        
    def test_one_command(self):
        rsp = Response("{01;FB;18|64:SAL=0|04B1}")
        cmdDict = rsp.getCommands()
        rsp_ref = {'SAL': ['0']}
        self.assertDictEqual(cmdDict, rsp_ref)

    def test_multiple_commands(self):
        rsp = Response("{01;FB;3B|64:TNF=138C;UDC=CDD;UGD=766;UL1=92B;UM1=928|0D73}")

        cmdDict = rsp.getCommands()
        rsp_ref = {'TNF': ['138C'], 'UDC': ['CDD'], 'UGD': ['766'], 'UL1': ['92B'], 'UM1': ['928']}
        self.assertDictEqual(cmdDict, rsp_ref)

    def test_one_command_multiple_values(self):
        rsp = Response("{01;FB;1D|64:SYS=4E24,0|05E7}")

        cmdDict = rsp.getCommands()
        rsp_ref = {'SYS': ['4E24', '0']}
        self.assertDictEqual(cmdDict, rsp_ref)

    def test_multiple_values(self):
        rsp = Response("{01;FB;48|64:SDAT=7DC0219,E050;SNM=FF,FF,FF,0;SRD=0;SRS=0;TCP=3039|107D}")

        cmdDict = rsp.getCommands()
        rsp_ref = {'SDAT': ['7DC0219', 'E050'], 'SNM': ['FF', 'FF', 'FF', '0'], 'SRD': ['0'], 'SRS': ['0'], 'TCP': ['3039']}
        self.assertDictEqual(cmdDict, rsp_ref)

    def test_add_block_ok(self):
        rsp = Response("{01;FB;1B|64:SDAT=7DC|595}")
        rsp.addBlock("{01;FB;40|64:0219,E050;SNM=FF,FF,FF,0;SRD=0;SRS=0;TCP=3039|0E4E}")

        cmdDict = rsp.getCommands()
        rsp_ref = {'SDAT': ['7DC0219', 'E050'], 'SNM': ['FF', 'FF', 'FF', '0'], 'SRD': ['0'], 'SRS': ['0'], 'TCP': ['3039']}
        self.assertDictEqual(cmdDict, rsp_ref)

    def test_add_block_error(self):
        with self.assertRaises(MessageDataException):
            rsp = Response("{01;FB;27|64:SDAT=7DC}")

        with self.assertRaises(MessageDataException):
            rsp = Response("{01;FB;27|64:SDAT=7DC|058B}")
            rsp.addBlock("{0219,E050;SNM=FF,FF,FF,0;SRD=0;SRS=0;TCP=3039|0DAD}")

    def test_split_response(self):
        rsp = Response("{01;FB;FF|64:EC00=7DF0C14,81E0,4E28,0;EC01=7DF0C14,816F,4E22,0;EC02=7DF0C14,8133,4E28,0;EC03=7DF0C14,8067,4E23,0;EC04=7DF0C13,EA6F,4E22,0;EC05=7DF0C13,7E4A,4E28,0;EC06=7DF0C13,7D68,4E22,0;EC07=7DF0C13,7D2C,4E28,0;EC08=7DF0C13,79F2,4E23,0;EC09=7DF0C1|3748)")
        rsp.addBlock("{01;FB;1D|2,EA09,4E22,0|057E}")
        
        cmdDict = rsp.getCommands()
        print(cmdDict)
        rsp_ref = {'EC08': ['7DF0C13', '79F2', '4E23', '0'], 'EC09': ['7DF0C12', 'EA09', '4E22', '0'], 'EC00': ['7DF0C14', '81E0', '4E28', '0'], 'EC01': ['7DF0C14', '816F', '4E22', '0'], 'EC02': ['7DF0C14', '8133', '4E28', '0'], 'EC03': ['7DF0C14', '8067', '4E23', '0'], 'EC04': ['7DF0C13', 'EA6F', '4E22', '0'], 'EC05': ['7DF0C13', '7E4A', '4E28', '0'], 'EC06': ['7DF0C13', '7D68', '4E22', '0'], 'EC07': ['7DF0C13', '7D2C', '4E28', '0']}
        self.assertDictEqual(cmdDict, rsp_ref)
        
        
if __name__ == '__main__':
    unittest.main()
