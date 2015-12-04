# -*- coding: utf-8 -*-

import unittest
from DataConverter import DataConverter
from Command import Command

#===============================================================================
# Logging
#===============================================================================
import logging
logging.basicConfig(level=logging.INFO)


class TestConverter(unittest.TestCase):
    def test_convertSYS(self):
        dc = DataConverter()
        cmds = {'SYS': ['4E24', '0']}
        
        result = dc.convertValues(cmds)
        
        self.assertEqual(result[0].Name, 'SYS')
        self.assertEqual(result[0].Value, 'Exploitation MPP')

    def test_convertType(self):
        dc = DataConverter()
        cmds = {'TYP': ['4E34']}
        
        result = dc.convertValues(cmds)
        
        self.assertEqual(result[0].Name, 'TYP')
        self.assertEqual(result[0].Value, 'SolarMax 3000 S')

    def test_convertDate(self):
        dc = DataConverter()
        cmds = {'FRD': ['7DB0206']}
        
        result = dc.convertValues(cmds)
        
        self.assertEqual(result[0].Name, 'FRD')
        self.assertEqual(result[0].Value, '2011-02-06')

    def test_convertD2(self):
        dc = DataConverter()
        cmds = {'PAC': ['D16']}
        
        result = dc.convertValues(cmds)
        
        self.assertEqual(result[0].Name, 'PAC')
        self.assertEqual(result[0].Value, '1675.0')

    def test_convertD10(self):
        dc = DataConverter()
        cmds = {'UL1': ['92B']}
        
        result = dc.convertValues(cmds)
        
        self.assertEqual(result[0].Name, 'UL1')
        self.assertEqual(result[0].Value, '234.7')

    def test_convertD100(self):
        dc = DataConverter()
        cmds = {'IL1': ['2D1']}
        
        result = dc.convertValues(cmds)
        
        self.assertEqual(result[0].Name, 'IL1')
        self.assertEqual(result[0].Value, '7.21')
        
    def test_convertX1(self):
        dc = DataConverter()
        cmds = {'PRL': ['3A']}
        
        result = dc.convertValues(cmds)
        
        self.assertEqual(result[0].Name, 'PRL')
        self.assertEqual(result[0].Value, '58')
        
    def test_convertX100(self):
        dc = DataConverter()
        cmds = {'KDY': ['2D']}
        
        result = dc.convertValues(cmds)
        
        self.assertEqual(result[0].Name, 'KDY')
        self.assertEqual(result[0].Value, '4500')

    def test_convertError(self):
        dc = DataConverter()
        cmds = {'EC00': ['7DC0219', '1234', '4E22']}
        
        result = dc.convertValues(cmds)
        
        self.assertEqual(result[0].Name, 'EC00')
        self.assertEqual(result[0].Value, ('2012-02-25', '01:17:40', 20002, 'Rayonnement trop faible'))
        
    def test_convertDateEnergy(self):
        dc = DataConverter()
        cmds = {'DD00': ['7DC0219', '2D', '14E0', '4D']}
        
        result = dc.convertValues(cmds)
        
        self.assertEqual(result[0].Name, 'DD00')
        self.assertEqual(result[0].Value, ('2012-02-25', '4.5', '2672.0', '7.7'))
