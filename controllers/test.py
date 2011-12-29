# -*- coding: utf-8 -*-

"""
    This file is used to test out various ideas or new Web2Py features
"""

module = "test"
s3_menu(module)

def index():
    "Shows request/session state for debugging"
    return dict()

def call():
    "Call an XMLRPC, JSONRPC or RSS service"
    # If webservices don't use sessions, avoid cluttering up the storage
    #session.forget()
    return service()

def test():
    #items =
    #db.atable.afield.readable = db.atable.afield.writable = False
    #db.atable.afield.default = "default!"
    crud.settings.create_next = "test/[id]"
    form = crud.create(db.atable)
    return dict(form=form)

def webgrid():
    table = db.gis_feature_class
    webgrid = local_import('webgrid')
    grid = webgrid.WebGrid(crud)
    grid.datasource = db(table.id > 0)
    # We want client-side paging
    grid.pagesize = 0
    # dataTables off to start with
    #grid.id = 'myTable'
    # No add_links as they interfere with dataTables
    #grid.enabled_rows = ['header', 'totals', 'pager', 'footer']

    # Show Edit/Delete links based on whether user can access them:
    grid.action_links = ['view']
    grid.action_headers = ['']
    #if auth.s3_has_permission('update', table):
    #    grid.action_links.append('edit')
    #if auth.s3_has_permission('delete', table):
    #    grid.action_links.append('delete')

    return dict(grid=grid())

def post():
    """Test for JSON POST
    #curl -i -X POST http://127.0.0.1:8000/sahana/test/post -H "Content-Type: application/json" -d {"name": "John"}
    #curl -i -X POST http://127.0.0.1:8000/sahana/test/post -H "Content-Type: application/json" -d @test.json
    Web2Py forms are multipart/form-data POST forms
    curl -i -X POST http://127.0.0.1:8000/sahana/test/post -F name=john
    curl -i -X POST --data-urlencode "name=Colombo Shelter" http://127.0.0.1:8000/sahana/test/post
    """
    #file=request.body.read()
    #reader=json.loads(file)
    #name = reader["name"]
    #return db.test_post.insert(name=name)
    return db.test_post.insert(**dict (request.vars))

def get():
    """Test for JSON GET
    curl -i http://127.0.0.1:8000/sahana/test/get -F name=john
    """
    #return db.test_get.insert(**json.loads(request.vars.fields))
    return db.test_get.insert(**dict (request.vars))

def refresh():
    response.refresh = '<noscript><meta http-equiv="refresh" content="2; url=' + URL(c='budget',f='item') + '" /></noscript>'
    return dict()

def photo():
    form = crud.create(db.test_photo)
    return dict(form=form)

def user():
    if auth.is_logged_in() or auth.basic():
        user = auth.user.id if session.auth else 0
    else:
        user = None
    return user

def css():
    items = crud.select(db.pr_person, _id='myid', _class='myclass')
    form = crud.create(db.pr_person)
    form['_class'] = 'my2class'
    form['_id'] = 'my2id'
    return dict(items=items, form=form)

def type():
    table = db.msg_group_type
    table.name.represent = T
    items = crud.select(table)
    table = db.msg_group
    form = crud.create(table)
    return dict(form=form, items=items)

