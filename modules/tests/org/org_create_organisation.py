from gluon import current
from tests.web2unittest import SeleniumUnitTest

class org_create_organisation(SeleniumUnitTest):
    def test_create_organisation(self, items=[0]):
        """
            Create an Organisation
            
            @param items: Organisation(s) to create from the data

            @ToDo: currently optimised for a single record
        """
        print "\n"

        # Configuration
        tablename = "org_organisation"
        url = "org/organisation/create"
        account = "normal"
        data = current.data["organisation"]

        # Login, if not-already done so
        self.login(account=account, nexturl=url)

        for item in items:
            _data = data[item]
            # Check whether the data already exists
            s3db = current.s3db
            db = current.db
            table = s3db[tablename]
            fieldname = _data[0][0]
            value = _data[0][1]
            query = (table[fieldname] == value) & (table.deleted == "F")
            record = db(query).select(table.id,
                                      limitby=(0, 1)).first()
            if record:
                print "org_create_organisation skipped as %s already exists in the db\n" % value
                return False

            # Create a record using the data
            result = self.create(tablename, _data)

# END =========================================================================
