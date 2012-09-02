""" Sahana Eden Module Automated Tests - Test Roles

    @copyright: 2012 (c) Sahana Software Foundation
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

import os

from gluon import current
from gluon.storage import Storage

import unittest
from tests.web2unittest import SeleniumUnitTest
#from tests import *
#import unittest, re, time

def create_role_test_data():
    from lxml import etree
    import StringIO

    db = current.db
    s3db = current.s3db
    auth = current.auth
    s3mgr = current.manager
    request = current.request

    # Define Organisations
    orgs = ["Org-A",
            "Org-B",
            "Org-C",
            ]
    branches = [ None,
                 "Branch-A"]

    #----------------------------------------------------------------------
    # Initialize Data & Users
    auth.override = True
    s3db.load_all_models()

    test_dir = os.path.join( current.request.folder,"modules",
                             "tests", "roles",
                             current.deployment_settings.base.template)

    data_file = open(os.path.join(test_dir, "data.xml"), "rb")
    data_template_string = data_file.read()
    org_resource = s3db.resource("org_organisation")

    user_file = open(os.path.join(test_dir, "users_template.csv"), "rb")
    user_template_string = user_file.read()

    # Ensure that the users are imported correctly
    s3db.configure( "auth_user",
                    onaccept = lambda form: auth.s3_link_user(form.vars))
    s3db.add_component("auth_membership", auth_user="user_id")
    s3mgr.import_prep = auth.s3_membership_import_prep

    user_resource = s3db.resource("auth_user")
    hr_resource = s3db.resource("pr_person")

    user_file = StringIO.StringIO()
    user_stylesheet = os.path.join(current.request.folder,"static", "formats",
                                   "s3csv", "auth", "user.xsl")
    hr_stylesheet = os.path.join(current.request.folder,"static", "formats", "s3csv", "hrm", "person.xsl")

    for org in orgs:
        for branch in branches:

            # Get the "Other" Orgs
            copy_orgs = list(orgs)
            copy_orgs.remove(org)
            orgx1 = copy_orgs[0]
            orgx2 = copy_orgs[1]

            if branch:
                org = "%s-%s" % (org,branch)

             # Create Test Data for each Organisation
            data_string = data_template_string % dict( org = org,
                                                       orgx1 = orgx1,
                                                       orgx2 = orgx2,
                                                       )
            xmltree = etree.ElementTree( etree.fromstring(data_string) )
            success = org_resource.import_xml(xmltree)

            # Create Users for each Organisation
            user_string = user_template_string % dict(org = org)
            user_file = StringIO.StringIO(user_string)
            success = user_resource.import_xml(user_file,
                                               format="csv",
                                               stylesheet=user_stylesheet)
            user_file = StringIO.StringIO(user_string)
            hr_resource.import_xml(user_file, format="csv", stylesheet=hr_stylesheet)
            #print success

    db.commit()
    auth.override = False

#----------------------------------------------------------------------
# Test Permissions against Role Matrix File
def test_roles():
    import csv

    s3db = current.s3db
    db = current.db

    suite = unittest.TestSuite()

    orgs = ["Org-A"]
    table_lookup = {"hrm_staff":"hrm_human_resource",
                    "vol_volunteer":"hrm_human_resource",
                    "inv_warehouse":"org_office"
                    }

    for org in orgs:
        permission_matrix_filename = os.path.join(current.request.folder,"modules", "tests", "roles",
                                                  current.deployment_settings.base.template, "%s_permission_matrix.csv" % org)
        permission_matrix_file = open(permission_matrix_filename, "rb")
        permission_matrix = csv.DictReader(permission_matrix_file)
        row_num = 1 # Header Row
        for test in permission_matrix:
            row_num = row_num + 1

            #if row_num < 0 or row_num > 10:
            #    continue
            table = test["table"]
            c = test["c"]
            f = test["f"]
            method = test["method"]
            uuid = test["uuid"]
            if table:
                db_table = s3db[table]
            elif c and f:
                db_table =  s3db[table_lookup["%s_%s" % (c,f)]]
            else:
                # No Table or C and F
                continue
            if uuid:
                record_id = db(db_table.uuid==uuid).select(db_table._id, limitby=(0,1)).first()[db_table._id]
            else:
                record_id = None

            for user, permission in test.items():
                if user in ["table","c", "f", "method", "uuid"] or not user:
                    continue
                test_role = TestRole()
                test_role.set(org = org,
                              row_num = row_num,
                                     user = user,
                                     method = method,
                                     table = table,
                                     c = c,
                                     f = f,
                                     record_id = record_id,
                                     uuid = uuid,
                                     permission = permission)
                suite.addTest(test_role)

    return suite
    #self.assertFalse(permitted)
    #self.assertTrue(False,"This Should have been True")

class TestRole(SeleniumUnitTest):
    def set(self,
            org,
            row_num,
                 user,
                 method,
                 table,
                 c,
                 f,
                 record_id,
                 uuid,
                 permission):
        self.org = org
        self.row_num = row_num
        self.user = user
        self.method = method
        self.table = table
        self.c = c
        self.f = f
        self.record_id = record_id
        self.uuid = uuid
        self.permission = permission

    def runTest(self):
        auth = current.auth

        org = self.org
        row_num = self.row_num
        user = self.user
        method = self.method
        table = self.table
        c = self.c
        f = self.f
        record_id = self.record_id
        uuid = self.uuid
        permission = self.permission

        auth.s3_impersonate(user)
        permitted = auth.permission.has_permission(method = method,
                                           t = table,
                                           c = c,
                                           f = f,
                                           record = record_id)
        msg = """Permission Error
Organisation:%s (Row:%s)
user:%s
table: %s\tc: %s\tf: %s\tmethod: %s\tuuid: %s\tid: %s
Expected: %s\t Actual: %s
""" % (org, row_num,
       user,
       table, c, f, method, uuid, record_id,
       permission == "Yes", permitted
       )
        self.assertEqual(permission == "Yes", permitted, msg)
        print msg
        #----------------------------------------------------------------------

    def dummy_code(self):
        #resource = current.s3db.resource("org_organisation", uid="Org-A")
        #resource.load()
        self.assertEqual(len(resource), 1)
        record = resource._rows[0]
        self.assertEqual(record.name, "Org-A")

        resource = current.s3db.resource("org_organisation", uid="Office-A")
        resource.load()
        self.assertEqual(len(resource), 1)
        record = resource._rows[0]
        self.assertEqual(record.name, "Office-A")

        resource = current.s3db.resource("org_organisation", uid="InvItem-A")
        resource.load()
        self.assertEqual(len(resource), 1)
        record = resource._rows[0]
        self.assertEqual(record.quantity, 10)

        resource = current.s3db.resource("org_organisation", uid="Item-A")
        resource.load()
        self.assertEqual(len(resource), 1)
        record = resource._rows[0]
        self.assertEqual(record.name, "Item-A")

        #for org in orgs:

        #    data_ids[org] = Storage()
        #    for table_name, value in org_data:
        #        # Unique name for each Org
        #        value = "%s %s" % (org, value)
        #        field_name = "name"
        #        values = {field_name: value}

        #        if not id:
        #            table = db[table_name]
        #            field = table[field_name]
        #            id = db(field == value).select(db[table_name].id).first().id
        #        data_ids[org][value] = id
        #print data_ids
        #db.commit()
