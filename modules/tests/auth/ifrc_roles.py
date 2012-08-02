""" Sahana Eden Module Automated Tests - IFRC Roles

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

from tests.web2unittest import SeleniumUnitTest
from tests import *
from gluon import current
from gluon.storage import Storage
#import unittest, re, time

class IFRCRoles(SeleniumUnitTest):
    def test_ifrc_roles(self):
        
        """
            @case: -
            @description: Test IFRC Roles between multiple organisations
            
            @Test Wiki: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Testing
        """
        #auth.s3_impersonate("survey_reader@example.com")
        #permitted = auth.s3_has_permission("create", table="survey_series")
        #self.assertFalse(permitted)
        #self.assertTrue(False,"This Should have been True")
        
        from lxml import etree
        import os
        import StringIO
        import csv
        
        s3db = current.s3db
        db = current.db
        auth = current.auth
        s3mgr = current.manager
        
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

        data_file = open(os.path.join(current.request.folder,"modules", "tests", "auth", "ifrc_data.xml"), "rb")
        data_template_string = data_file.read()
        org_resource = s3mgr.define_resource("org", "organisation")
        
        user_file = open(os.path.join(current.request.folder,"modules", "tests", "auth", "ifrc_users.csv"), "rb")
        user_template_string = user_file.read()
        user_resource = s3mgr.define_resource("auth", "user")
        user_file = StringIO.StringIO()
        user_stylesheet = os.path.join(current.request.folder,"static", "formats", "s3csv", "auth", "user.xsl")
        
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
        
        auth.override = False
        
        #----------------------------------------------------------------------
        # Test Permissions against Role Matrix File
        orgs = ["Org-A"]
        table_lookup = {"hrm_staff":"hrm_human_resource",
                        "vol_volunteer":"hrm_human_resource",
                        "inv_warehouse":"org_office"
                        }
        for org in orgs:
            permission_matrix_filename = os.path.join(current.request.folder,"modules", "tests", "auth", "%s_permission_matrix.csv" % org)
            permission_matrix_file = open(permission_matrix_filename, "rb")
            permission_matrix = csv.DictReader(permission_matrix_file)
            row_num = 1 # Header Row
            for test in permission_matrix:
                row_num = row_num + 1
                table = test["table"]
                c = test["c"]
                f = test["f"]
                method = test["method"]
                uuid = test["uuid"]
                if table:
                    db_table = s3db[table] 
                else:
                    db_table =  s3db[table_lookup["%s_%s" % (c,f)]]
                if uuid:
                    id = db(db_table.uuid==uuid).select(db_table._id, limitby=(0,1)).first()[db_table._id]
                else:
                    id = None
                    
                for user, permission in test.items():
                    if user in ["table","c", "f", "method", "uuid"]:
                        continue
                    auth.s3_impersonate(user.lower())
                    permitted = auth.s3_has_permission(method, 
                                                       table="survey_series",
                                                       c = c,
                                                       f = f,
                                                       record_id = id)
                    msg = """Permission Error
Permissions Matrix File:%s (Row:%s)
user:%s
table: %s\tc: %s\tf: %s\tmethod: %s\tuuid: %s\tid: %s
Expected: %s\t Actual: %s 
""" % (permission_matrix_filename, row_num,
       user,
       table, c, f, method, uuid, id,
       permission == "Yes", permitted
       )
                    self.assertEqual(permission == "Yes", permitted, msg) 
        #self.assertFalse(permitted)
        #self.assertTrue(False,"This Should have been True")

        
        #----------------------------------------------------------------------
        

    def dummy_code(self):
        #resource = s3mgr.define_resource("org", "organisation", uid="Org-A")
        #resource.load()
        self.assertEqual(len(resource), 1)
        record = resource._rows[0]
        self.assertEqual(record.name, "Org-A")
        
        resource = s3mgr.define_resource("org", "office", uid="Office-A")
        resource.load()
        self.assertEqual(len(resource), 1)
        record = resource._rows[0]
        self.assertEqual(record.name, "Office-A")
        
        resource = s3mgr.define_resource("inv", "inv_item", uid="InvItem-A")
        resource.load()
        self.assertEqual(len(resource), 1)
        record = resource._rows[0]
        self.assertEqual(record.quantity, 10)
        
        resource = s3mgr.define_resource("supply", "item", uid="Item-A")
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
        



