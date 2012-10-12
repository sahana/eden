if not request.env.web2py_runtime_gae:
    db = DAL("sqlite://storage.sqlite")
else:
    db = DAL("google:datastore")
    session.connect(request, response, db=db)

# This should detect one table disappeared, one field disappeared and one field added
db.define_table("main",
                Field("remove_name")
                )

# This should detect one field disappeared and one field added
db.define_table("renaming",
                Field("renamed2")
                )

# This should detect one field disappeared, one field added and one table added
db.define_table("edit",
                Field("new_id", "integer"),
                Field("name",
                      default = "1")
                )
db.define_table("added",
                Field("name")
                )

# END =========================================================================
