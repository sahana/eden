# Script to import all, copy & paste, then run (on server)
# imp_eric(local = False) 

# import_eric(True, "eric_sample.csv") will take ~12 sec to import 500 Items

def import_eric(local = False, file_name = "eric_complete.csv"):
    import time
    secs = time.mktime(time.localtime())
    auth.environment.session.auth = True
    session.s3.roles.append(ADMIN)
    if local:
        import_dir = "C:\\bin\\web2py\\applications\\eden\\static\\formats\\s3csv\\"
    else:
        import_dir = "/home/web2py/applications/eden/static/formats/s3csv/"
    
    resource = s3mgr.define_resource("supply", "item_category")
    resource.import_xml(open("%s%s" % (import_dir, "eric_supply_item_category.csv"), "r"),
                        format="csv",
                        stylesheet="%s%s" % (import_dir, "eric_supply_item_category.xsl") )
    
    resource = s3mgr.define_resource("supply", "item")
    resource.import_xml(open("%s%s" % (import_dir, file_name), "r"),
                        format="csv",
                        stylesheet="%s%s" % (import_dir, "eric.xsl") )
    db.commit()
    print "Total Time: %s" % (time.mktime(time.localtime()) - secs)