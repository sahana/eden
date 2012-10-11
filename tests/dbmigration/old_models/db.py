if not request.env.web2py_runtime_gae:
    db = DAL("sqlite://storage.sqlite")
else:
    db = DAL("google:datastore")
    session.connect(request, response, db=db)

# Test for removing a table, this table is removed in the next revision
db.define_table("removing",
                Field("name")
                )

db.define_table("main",
                Field("remove_id", "integer")
                )

# Test for renaming a field
db.define_table("renaming",
                Field("renamed")
                )

# Test for adding and deleting a field
db.define_table("edit",
                Field("name", "integer",
                      default="2")
                )

# END =========================================================================
