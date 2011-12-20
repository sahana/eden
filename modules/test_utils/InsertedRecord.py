
from clear_table import clear_table

class InsertedRecord(object):
    """Inserts and commits a record and removes it at the end of
    a test no matter what happens.
    
    """
    def __init__(self, db, table, data):
        self.db = db
        self.table = table
        self.data = data
    
    def __enter__(self):
        self.table.insert(**self.data)
        self.db.commit()
        
    def __exit__(self, type, value, traceback):
        clear_table(self.db, self.table)
