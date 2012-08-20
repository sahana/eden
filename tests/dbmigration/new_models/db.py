if not request.env.web2py_runtime_gae:
    db = DAL('sqlite://storage.sqlite')
else:
    db = DAL('google:datastore')
    session.connect(request, response, db = db)
"""
Database for testing purpose
"""
#This should detect one table disappeared , one field disapperaed and one field added
db.define_table('main',Field('remove_name','string'))

#This should detect one field disappeared and one field added
db.define_table('renaming',Field('renamed2','string'))

#This should detect one field disappered , one field added and on table added
db.define_table('edit',Field('new_id','integer'),Field('name','string',default = "1"))
db.define_table('added',Field('name','string'))
