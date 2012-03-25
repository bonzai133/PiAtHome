# Test avec sqlite3

import sqlite3, sys

class GlobalData:
    """Contains global vars"""
    dbFileName = "Solarmax_data.s3db"
    
    #Structure of database
    dbTables = { 
        "EnergyByYear":[('date', "d", "Date"),
                        ('year', "n", "Year"), 
                        ('energy', "r", "Energy in kWh"),
                        ('peak', "r", "Peak energy in W"),
                        ('hours', "r", "Hours of sunshine")],
                        
        "EnergyByMonth":[('date', "d", "Date"),
                        ('year', "n", "Year"), 
                        ('month', "n", "Month"), 
                        ('energy', "r", "Energy in kWh"),
                        ('peak', "r", "Peak energy in W"),
                        ('hours', "r", "Hours of sunshine")],
                         
        "EnergyByDay":[    ('date', "d", "Date"), 
                        ('year', "n", "Year"), 
                        ('month', "n", "Month"), 
                        ('day', "n", "Day"), 
                        ('energy', "r", "Energy in kWh"),
                        ('peak', "r", "Peak energy in W"),
                        ('hours', "r", "Hours of sunshine")]}

class DBManager:
    """Management of a MySQL database"""
    
    def __init__(self, dbFileName):
        "Connect and create the cursor"
        try:
            self.connection = sqlite3.connect(dbFileName)
        except Exception, err:
            print "DB Connect failed: %s" % err
            self.connectFailure =1
        else:
            self.cursor = self.connection.cursor()
            self.connectFailure =0
    
    def CreateTables(self, dictTables):
        for table in dictTables.keys():
            req = "CREATE TABLE IF NOT EXISTS %s (" % table
            
            for descr in dictTables[table]:
                fieldName = descr[0]
                fType = descr[1]
                
                if fType == 'n':
                    fieldType = 'INTEGER'
                elif fType == 'r':
                    fieldType = 'REAL'
                elif fType == 'd':
                    fieldType = 'TEXT PRIMARY KEY'
                else:
                    fieldType = 'BLOB'
                    
                req = req + "%s %s, " % (fieldName, fieldType)
                
            req = req[:-2] + ")"
                
            self.ExecuteRequest(req)
                
        
    def DeleteTables(self, dictTables):
        for table in dictTables.keys():
            req = "DROP TABLE %s" % table
            self.ExecuteRequest(req)
        self.Commit()            
    
    def ExecuteRequest(self, req):
        #print req
        try:
            self.cursor.execute(req)
        except Exception, err:
            print "Incorrect SQL request (%s)\n%s" % (req, err)
            return 0
        else:    
            return 1
    
    def GetResult(self):
        return self.cursor.fetchall()
        
    def Commit(self):
        if self.connection:
            self.connection.commit()
                    
    def Close(self):
        if self.connection:
            self.connection.close()
        
def main(argv):
    #Connect to the database
    dbm = DBManager(GlobalData.dbFileName)
    if dbm.connectFailure == 1:
        print "Can't connect to database"
    else:
        dbm.CreateTables(GlobalData.dbTables)
        print "TODO : work on the DB"
    
    dbm.Close()
    
    
    
if __name__ == "__main__":
    main(sys.argv[1:])
