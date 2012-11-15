auth.override = True

# Ensure that the users are imported correctly
s3db.configure( "auth_user",
                onaccept = lambda form: auth.s3_approve_user(form.vars))
s3db.add_component("auth_membership", auth_user="user_id")
s3mgr.import_prep = auth.s3_membership_import_prep
#user_filename = os.path.join("/code","sandbox", "test_users.csv")
user_filename = os.path.join(current.request.folder,"private", "templates", "IFRC_Train", "users.csv")
user_filename = os.path.join(current.request.folder,"modules", "tests", "roles", "IFRC", "test_users.csv")
user_file = open(user_filename, "rb")

user_resource = s3db.resource("auth_user")
person_resource = s3db.resource("pr_person")
user_stylesheet = os.path.join(current.request.folder,"static", "formats",
                               "s3csv", "auth", "user.xsl")
hr_stylesheet = os.path.join(current.request.folder,"static", "formats", "s3csv", "hrm", "person.xsl")

# Create Users for each Organisation
#success = user_resource.import_xml(user_file,
#                                   format="csv",
#                                   stylesheet=user_stylesheet)
user_file = open(user_filename, "rb")
success = person_resource.import_xml(user_file, format="csv", stylesheet=hr_stylesheet)
db.commit()
exit()


def pe_name(pe_id):
    try:
        name = db(pt.pe_id == pe_id).select().first().first_name
    except:
        pass
    try:
        name = db(oft.pe_id == pe_id).select().first().name
    except:
        pass
    try:
        name = db(ort.pe_id == pe_id).select().first().name
    except:
        pass
    try:
        name = db(wt.pe_id == pe_id).select().first().name
    except:
        pass
    print name

def role_test(current,
              user,
              method,
              table = None,
              c = None,
              f = None,
              record_id = None,
              ):
    auth = current.auth
    auth.override = False
    auth.s3_impersonate(user)
    permitted = auth.permission.has_permission(method = method, 
                                       t = table,
                                       c = c,
                                       f = f,
                                       record = record_id)
    return permitted
permitted = role_test(current, "staff_editor@org-a.com", "read", c= "org", f = "organisation",  table = "org_organisation", record_id = 42)
permitted = role_test(current, "warehouse-a@org-a.com", "read", table = "pr_person", record_id = 295)
permitted = role_test(current, "staff_data_entry@org-a.com", "update",  table = "org_organisation", record_id = 42)
print permitted

#permitted = role_test(current, "staff_super@org-a.com", "create", c= "hrm", f = "staff")
permitted = role_test(current, "branch-a@org-a.com", "update", c= "hrm", f = "staff",  table = "pr_education", record_id = 1)
print permitted

permitted = role_test(current, "branch-a@org-a.com", "update", c= "hrm", f = "staff",  table = "pr_physical_description", record_id = 2)
print permitted

auth.override = True
s3db.load_all_models()
for tablename in db.tables():
    table = db[tablename]
    if not "realm_entity" in table.fields:
        print "NO   " + tablename
    elif not db(table.id > 0).count():
        print "EMPT " + tablename
    elif db(table.realm_entity == None).count():
        print "NONE " + tablename
    else:
        print "FULL " + tablename
        


resource = s3db.resource("org", "organisation")
import_file = os.path.join("/Users","michaelhowden","Documents","AidIQ","Projects","IFRC","RMS 2.0","NS","AusRC","Import", "AusRC_branch.csv")
File = open(import_file, "r")
stylesheet = os.path.join(request.folder, "static", "formats",
"s3csv", "org", "organisation.xsl")
resource.import_xml(File, format="csv", stylesheet=stylesheet)
db.commit()

"""

#permitted = role_test(current, "staff_super@org-a.com", "create", c= "hrm", f = "staff")

role_test(current, "vol_super@org-a.com", "create", c= "vol", f = "volunteer")


role_test(current, "irs_super@Org-A.com", "create", c= "org", f = "organisation")
#print permitted
user_filename = os.path.join(current.request.folder,"modules", "tests", "auth", current.deployment_settings.base.template, "test_users_x.csv")
user_file = open(user_filename, "rb")
user_stylesheet = os.path.join(current.request.folder,"static", "formats", "s3csv", "auth", "user.xsl")
#def auth_user_onaccept(form):
#    auth = current.auth
#    return auth.s3_link_to_person(user=form.vars)
#s3db.configure("auth_user",
#               onaccept = auth.s3_register)
auth = current.auth
s3db.configure("auth_user",
                onaccept = lambda form: auth.s3_link_user(form.vars))
#s3db.configure("auth_membership",
#                onvalidation = auth.s3_membership_onvalidation)

s3db.add_component("auth_membership", auth_user="user_id")
user_resource = s3mgr.define_resource("auth", "user")
auth.override = True
s3mgr.import_prep = auth.s3_membership_import_prep
print user_resource.import_xml(user_file, format="csv", stylesheet=user_stylesheet, ignore_errors=True)
s3mgr.import_prep = None

# Redefine because import clears the file buffer
user_file = open(user_filename, "rb")
hr_stylesheet = os.path.join(current.request.folder,"static", "formats", "s3csv", "hrm", "person.xsl")
hr_resource = s3mgr.define_resource("pr", "person")
print hr_resource.import_xml(user_file, format="csv", stylesheet=hr_stylesheet)
db.commit()


/usr/bin/python static/scripts/tools/csv2xml.py modules/tests/auth/IFRC/test_users_y.csv static/formats/s3csv/auth/user.xsl > test.xml
/usr/bin/python static/scripts/tools/csv2xml.py modules/tests/auth/IFRC/test_users.csv static/formats/s3csv/hrm/person.xsl

"""