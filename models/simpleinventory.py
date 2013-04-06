
tablename = "simpleinventory_items"
table = db.define_table(tablename,
                        # Name of item
                        Field("name" , label=T("name")),
                        # The start time
                        Field("count","integer",label=T("count")),
                        # The facilitator
                        Field("status",label=T("status"),requires = IS_IN_SET(['need', 'noneed', 'urgent'])),
                        # This adds all the metadata to store
                        # information on who created/updated
                        # the record & when
                        *s3.meta_fields()
                        )
                        
LIST_ITEM =  T("List Items")
s3.crud_strings[tablename] = Storage(
    title_create = T("Add New item"),
    title_display = T("item status"),
    title_list = LIST_ITEM,
    title_update = T("Edit Item"),
    title_search = T("Search Item"),
   
    subtitle_create = T("Add New Item"),
    subtitle_list = T("Item"),
    label_list_button = LIST_ITEM,
    label_create_button = T("Add New Item"),
    label_delete_button = T("Delete Item"),
    msg_record_created = T("Item added"),
    msg_record_modified = T("Item updated"),
    msg_record_deleted = T("Item deleted"),
    msg_list_empty = T("No Item in inventory")) 
