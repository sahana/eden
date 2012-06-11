# Set up Offices
from gluon import current
from tests.web2unittest import SeleniumUnitTest

class org_create_office(SeleniumUnitTest):
    def test_create_office(self, items=[0]):
        """
            Create an Office
            
            @param items: Office(s) to create from the data
        """
        print "\n"

        # Configuration
        tablename = "org_office"
        url = "org/office/create"
        account = "normal"
        data = current.data["office"]

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
                print "org_create_office skipped as %s already exists in the db\n" % value
                return False

            # Create a record using the data
            result = self.create(tablename, _data)

# END =========================================================================
