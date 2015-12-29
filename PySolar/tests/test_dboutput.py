# -*- coding: utf-8 -*-

import unittest

from pysolarmax.DbOutput import DbOutput
from pysolarmax.Command import Command

#===============================================================================
# Logging
#===============================================================================
import logging
logging.basicConfig(level=logging.INFO)


#===============================================================================
# TestDbOutput
#===============================================================================
class TestDbOutput(unittest.TestCase):
    def test_connect_ok(self):
        out = DbOutput("test.s3db")
        res = out.TreatCommandsResults('Test', {'TST': Command('TST', 'Test command', None)})
        
        self.assertTrue(res)
    
    def test_connect_error(self):
        out = DbOutput("/notadir/test.s3db")
        res = out.TreatCommandsResults('Test', {'TST': Command('TST', 'Test command', None)})
        
        self.assertFalse(res)

    def test_realtime(self):
        out = DbOutput("test.s3db")
        cmd = Command('SYS', 'Operation State', None)
        cmd.Value = 'Test state'
        
        res = out.TreatCommandsResults('Realtime', {'SYS': cmd})
        
        self.assertTrue(res)
        self.assertEqual('REPLACE INTO Realtime (key, value, desc) VALUES ("SYS", "Test state", "Operation State")',
                         out.m_sqlRequestList[0])

    def test_statistics(self):
        out = DbOutput("test.s3db")
        cmd = Command('KHR', 'Operating hours', None)
        cmd.Value = '24823'
        
        res = out.TreatCommandsResults('Stats', {'KHR': cmd})
        
        self.assertTrue(res)
        self.assertEqual('REPLACE INTO Statistics (key, value, desc) VALUES ("KHR", "24823", "Operating hours")',
                         out.m_sqlRequestList[0])

    def test_errors(self):
        out = DbOutput("test.s3db")
        cmd = Command('EC00', 'Error 00', None)
        cmd.Value = ('2015-12-20', '09:14:08', 20008, 'Sur secteur')
        
        res = out.TreatCommandsResults('History', {'EC00': cmd})
        
        self.assertTrue(res)
        self.assertEqual('REPLACE INTO ErrorsHistory (datetime, errCode, desc) VALUES ("2015-12-20 09:14:08", "20008", "Sur secteur")',
                         out.m_sqlRequestList[0])
        
    def test_statsYear(self):
        out = DbOutput("test.s3db")
        cmd = Command('DY00', 'Energy by year', None)
        cmd.Value = ('2015-00-00', '3033.8', '3022.0', '4047.5')
        
        res = out.TreatCommandsResults('History', {'DY00': cmd})
        
        self.assertTrue(res)
        self.assertEqual('REPLACE INTO EnergyByYear (date, year, energy, peak, hours) VALUES ("2015-01-01", "2015", "3033.8", "3022.0", "4047.5")',
                         out.m_sqlRequestList[0])
    
    def test_statsMonth(self):
        out = DbOutput("test.s3db")
        cmd = Command('DM00', 'Energy by month', None)
        cmd.Value = ('2015-12-00', '61.7', '2166.0', '151.3')
        
        res = out.TreatCommandsResults('History', {'DM00': cmd})
        
        self.assertTrue(res)
        self.assertEqual('REPLACE INTO EnergyByMonth (date, year, month, energy, peak, hours) VALUES ("2015-12-01", "2015", "12", "61.7", "2166.0", "151.3")',
                         out.m_sqlRequestList[0])
            
    def test_statsDay(self):
        out = DbOutput("test.s3db")
        cmd = Command('DD00', 'Energy by day', None)
        cmd.Value = ('2015-12-20', '0.4', '190.0', '5.5')
        
        res = out.TreatCommandsResults('History', {'DD00': cmd})
        
        self.assertTrue(res)
        self.assertEqual('REPLACE INTO EnergyByDay (date, year, month, day, energy, peak, hours) VALUES ("2015-12-20", "2015", "12", "20", "0.4", "190.0", "5.5")',
                         out.m_sqlRequestList[0])
