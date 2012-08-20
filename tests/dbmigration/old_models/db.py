if not request.env.web2py_runtime_gae:
    db = DAL('sqlite://storage.sqlite')
else:
    db = DAL('google:datastore')
    session.connect(request, response, db = db)

"""
Database for testing purpose
"""
#Testing by removing a table , this table is removed in the next revivision
db.define_table('removing',Field('name','string'));
db.define_table('main',Field('remove_id','integer'))

#This table is used for renmaing a field
db.define_table('renaming',Field('renamed','string'));

#This table is used is used for adding and deleting a field
db.define_table('edit',Field('name','integer',default = "2"));
