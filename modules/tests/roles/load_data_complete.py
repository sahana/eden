""" Sahana Eden Module Automated Tests - Test Roles

    @copyright: 2012-2016 (c) Sahana Software Foundation
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

def create_role_test_data(orgs, branches):
    from lxml import etree
    import StringIO

    db = current.db
    s3db = current.s3db
    auth = current.auth
    request = current.request

    #----------------------------------------------------------------------
    # Initialize Data & Users
    auth.override = True
    s3db.load_all_models()

    test_dir = os.path.join( current.request.folder,"modules",
                             "tests", "roles",
                             current.deployment_settings.base.template)

    org_file = open(os.path.join(test_dir, "org_organisation.xml"), "rb")
    org_template_string = org_file.read()
    data_file = open(os.path.join(test_dir, "data.xml"), "rb")
    data_template_string = data_file.read()
    org_resource = s3db.resource("org_organisation")
    org_branch_file = open(os.path.join(test_dir, "org_organisation_branch.xml"), "rb")
    org_branch_template_string = org_branch_file.read()
    org_branch_resource = s3db.resource("org_organisation_branch")

    user_file = open(os.path.join(test_dir, "users_template.csv"), "rb")
    user_template_string = user_file.read()

    # Ensure that the users are imported correctly
    s3db.configure( "auth_user",
                    onaccept = lambda form: auth.s3_link_user(form.vars))
    s3db.add_components("auth_user", auth_membership="user_id")
    current.response.s3.import_prep = auth.s3_import_prep

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
                orgx = "%s-%s" % (org,branch)
            else:
                orgx = org
            #print orgx

            # Create Org & get id
            org_string = org_template_string % dict( org = orgx )
            xmltree = etree.ElementTree( etree.fromstring(org_string) )
            success = org_resource.import_xml(xmltree)
            otable = s3db.org_organisation
            org_id = db(otable.name == orgx).select(otable.id).first().id
            auth.user = Storage(organisation_id = org_id)

             # Create Test Data for each Organisation
            data_string = data_template_string % dict( org = orgx,
                                                       orgx1 = orgx1,
                                                       orgx2 = orgx2,
                                                       )
            xmltree = etree.ElementTree( etree.fromstring(data_string) )
            success = org_resource.import_xml(xmltree)

            # Create Users for each Organisation
            user_string = user_template_string % dict(org = orgx,
                                                      org_lower = orgx.lower())
            user_file = StringIO.StringIO(user_string)
            success = user_resource.import_xml(user_file,
                                               format="csv",
                                               stylesheet=user_stylesheet)
            user_file = StringIO.StringIO(user_string)
            hr_resource.import_xml(user_file, format="csv", stylesheet=hr_stylesheet)

            if branch:
                # Link Branch to Org
                org_branch_string = org_branch_template_string % dict( org = org,
                                                                 branch = branch
                                                                 )
                #print org_branch_string
                xmltree = etree.ElementTree( etree.fromstring(org_branch_string) )
                success = org_branch_resource.import_xml(xmltree)
                #print success

    # Import Test Users
    test_user_file = open(os.path.join(test_dir, "test_users.csv"), "rb")
    success = user_resource.import_xml(test_user_file,
                                       format="csv",
                                       stylesheet=user_stylesheet)
    test_user_file = open(os.path.join(test_dir, "test_users.csv"), "rb")
    hr_resource.import_xml(test_user_file, format="csv", stylesheet=hr_stylesheet)

    db.commit()
    auth.override = False

# Define Organisations
orgs = ["Org-A",
        "Org-B",
        "Org-C",
        ]
branches = [ None,
             "Branch-A"]

create_role_test_data(orgs,branches)
