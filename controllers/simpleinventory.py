module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

@auth.requires_login()
def items():
    return s3_rest_controller()
    
    
def index():
    db = current.db
    tablename = "simpleinventory_items"
    
    row1 = db(db.simpleinventory_items.status == 'need').select()
    row2 = db(db.simpleinventory_items.status == 'noneed').select()
    row3 = db(db.simpleinventory_items.status == 'urgent').select()
    
    
    
    return dict(red=row3 , yellow = row1 , green = row2)    
    
