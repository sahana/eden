""" Sahana Eden Automated Test - INV004 Create Warehouse

    @copyright: 2011-2012 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

from gluon import current

from tests.web2unittest import SeleniumUnitTest

class CreateWarehouse(SeleniumUnitTest):

    # -------------------------------------------------------------------------
    def test_inv004_create_warehouse(self, items=[0]):
        """
            Create a Warehouse

            @param items: Warehouse(s) to create from the data

            @TestDoc: https://docs.google.com/spreadsheet/ccc?key=0AmB3hMcgB-3idG1XNGhhRG9QWF81dUlKLXpJaFlCMFE
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """

        # Configuration
        tablename = "inv_warehouse"
        url = "inv/warehouse/create"
        account = "admin"
        data = [
    [
        # 1st field used to check whether record already exists
        ("name", "Bucharest RFAAT Central Warehouse (Test)"),
        ("code", "12345679"),
        ("organisation_id", "International Federation of Red Cross and Red Crescent Societies (IFRC)", "option"),
        ("comments", "This is a Test Warehouse"),
    ],
]

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
                print "inv004_create_warehouse skipped as %s already exists in the db\n" % value
                return False

            # Login, if not-already done so
            self.login(account=account, nexturl=url)

            # Create a record using the data
            result = self.create(tablename, _data)

            