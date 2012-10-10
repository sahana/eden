# -*- coding: utf-8 -*-
#
# REST Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3utils.py
#
import unittest
from gluon.dal import Query
from s3.s3utils import *

# =============================================================================
class S3FKWrappersTests(unittest.TestCase):

    def testHasForeignKey(self):

        ptable = s3db.pr_person
        self.assertFalse(s3_has_foreign_key(ptable.first_name))
        self.assertTrue(s3_has_foreign_key(ptable.pe_id))

        htable = s3db.hrm_human_resource
        self.assertFalse(s3_has_foreign_key(htable.start_date))
        self.assertTrue(s3_has_foreign_key(htable.person_id))

        otable = s3db.org_organisation
        self.assertTrue(s3_has_foreign_key(otable.multi_sector_id))
        self.assertFalse(s3_has_foreign_key(otable.multi_sector_id, m2m=False))

    def testGetForeignKey(self):

        ptable = s3db.pr_person
        ktablename, key, multiple = s3_get_foreign_key(ptable.pe_id)
        self.assertEqual(ktablename, "pr_pentity")
        self.assertEqual(key, "pe_id")
        self.assertFalse(multiple)

        otable = s3db.org_organisation
        ktablename, key, multiple = s3_get_foreign_key(otable.multi_sector_id)
        self.assertEqual(ktablename, "org_sector")
        self.assertEqual(key, "id")
        self.assertTrue(multiple)

        ktablename, key, multiple = s3_get_foreign_key(otable.multi_sector_id, m2m=False)
        self.assertEqual(ktablename, None)
        self.assertEqual(key, None)
        self.assertEqual(multiple, None)


# =============================================================================
class S3SQLTableTests(unittest.TestCase):

    def testHTML(self):
        # basic table
        cols = [{'name': 'col_1', 'label': u'Col 1'}]
        table = S3SQLTable(cols,
                           rows=[{'col_1': u'Val 1'}])

        self.assertEqual(unicode(table.xml()),
                         unicode(TABLE(THEAD(TR(TH(u"Col 1", _scope="col"))),
                                       TBODY(TR(TD(u"Val 1"))))))

        # limit
        table = S3SQLTable(cols,
                           rows=[{'col_1': u'Val 1'},
                                 {'col_1': u'Val 2'},
                                 {'col_1': u'Val 3'}],
                           limit=1)

        self.assertEqual(unicode(table.xml()),
                         unicode(TABLE(THEAD(TR(TH(u"Col 1", _scope="col"))),
                                       TBODY(TR(TD(u"Val 1"))))))


        cols = [{'name': 'id', 'label': u'Id'},
                {'name': 'col_1', 'label': u'Col 1'}]
        row_actions = [{"label": T("Activate"),
                        "url": URL(f="schedule_parser",
                                   args="[id]"),
                        "restrict": [1,]}]
        bulk_actions = [("delete", "Delete")]

        # bulk actions
        table = S3SQLTable(cols=cols[:],
                           rows=[{'id': 1, 'col_1': u'Val 1'}, {'id': 2, 'col_1': u'Val 2'}],
                           bulk_actions=bulk_actions)
        self.assertEqual(unicode(table.xml()),
                         unicode(FORM(SELECT(OPTION("", _value=""),
                                             OPTION("Delete", _value="delete"),
                                             _name="action"),
                                      INPUT(_type="submit", _value=T("Go")),
                                      TABLE(THEAD(TR(TH("Id", _scope="col"),
                                                     TH("Col 1", _scope="col"))),
                                            TBODY(TR(TD("1"),
                                                     TD("Val 1")),
                                                  TR(TD("2"),
                                                     TD("Val 2")))),
                                      _method="post",
                                      _action="")))

        # row actions
        table = S3SQLTable(cols=cols[:],
                           rows=[{'id': 1, 'col_1': u'Val 1'}, {'id': 2, 'col_1': u'Val 2'}],
                           row_actions=row_actions)
        self.assertEqual(unicode(table.xml()),
                         unicode(TABLE(THEAD(TR(TH("Id", _scope="col"),
                                                TH("Col 1", _scope="col"),
                                                TH(""))),
                                       TBODY(TR(TD("1"),
                                                TD("Val 1"),
                                                TD("")),
                                             TR(TD("2"),
                                                TD("Val 2"),
                                                TD(""))))))

    def testFromResource(self):
        # need to be logged in to query resources
        auth.s3_impersonate('admin@example.com')

        r = current.s3db.resource("org_organisation")
        table = S3SQLTable.from_resource(r,
                                         [{'name': 'id'}],
                                         limit=1)
        self.assertEqual(table.cols,
                         [{'name': 'id', 'label': u'Id', 'type': 'id'}])
        self.assertEqual(table.rows,
                         [{'id': u'1',}])

        # column label
        table = S3SQLTable.from_resource(r,
                                         [{'name': 'id', 'label': 'MyCol'}],
                                         limit=1)
        self.assertTrue(len(table.cols) == 1)
        self.assertTrue(len(table.rows) == 1)
        self.assertTrue(len(table.rows[0]) == 1)

        # foreign keys
        table = S3SQLTable.from_resource(r,
                                         [{'name': 'organisation_type_id$name'}],
                                         limit=2)
        self.assertTrue(len(table.rows) == 2)

# =============================================================================
class S3DataTableTests(unittest.TestCase):

    def testFromResource(self):
        # need to be logged in to query resources
        auth.s3_impersonate('admin@example.com')

        r = current.s3db.resource("org_organisation")

        # no limit
        table = S3DataTable.from_resource(r,
                                          [{'name': 'id'}])
        self.assertEqual(len(table.rows), r.count())

        # limit
        table = S3DataTable.from_resource(r,
                                          [{'name': 'id'}],
                                          limit=1)
        self.assertEqual(table.cols,
                         [{'name': 'id', 'label': 'Id', 'type': 'id'}])
        self.assertEqual(table.rows,
                         [{'id': u'1'},])

        # ajax source and page_size
        table = S3DataTable.from_resource(r,
                                          [{'name': 'id'}],
                                          options={'sAjaxSource': '_'},
                                          page_size=1)
        self.assertEqual(table.rows, [{'id': u'1'},])

        # ajax source, page_size and limit
        table = S3DataTable.from_resource(r,
                                          [{'name': 'id'}],
                                          options={'sAjaxSource': '_'},
                                          page_size=1,
                                          limit=2)
        self.assertEqual(len(table.rows), 1)

# =============================================================================
def run_suite(*test_classes):
    """ Run the test suite """

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    if suite is not None:
        unittest.TextTestRunner(verbosity=2).run(suite)
    return

if __name__ == "__main__":

    run_suite(
        S3FKWrappersTests,
        S3SQLTableTests,
        S3DataTableTests,
    )

# END ========================================================================
