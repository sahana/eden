import copy
import unittest

old_db_id = None
new_db_id = None
USE_TEST_DB = False
test_db_name = "testing.sqlite"

def make_test_db(DAL, db, clean):
    global new_db_id
    test_db = DAL("sqlite://%s" % test_db_name)
    new_db_id = id(test_db)
    # preserver hooks
    test_db.auth = db.auth
    test_db.manager = db.manager

    # Copy current db tables!
    for tablename in db.tables:
        table_copy = [copy.copy(f) for f in db[tablename]]
        test_db.define_table(tablename, *table_copy)

    if clean:
        # cleanup test_db
        for table_name in test_db.tables():
            test_db[table_name].truncate()

    return test_db

def get_db(DAL, current_db, clean=False):
    global old_db_id
    old_db_id = id(current_db)

    if USE_TEST_DB:
        print "preparing test db (%s)" % test_db_name
        return make_test_db(DAL, current_db, clean)
    return current_db

class DBReplicationTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_db_replication(self):
        if USE_TEST_DB:
            self.assertTrue(old_db_id != new_db_id)
        else:
            self.assertEqual(new_db_id, None)
