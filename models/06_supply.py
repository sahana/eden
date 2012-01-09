# -*- coding: utf-8 -*-

"""
    Supply

    @author: Michael Howden (michael@sahanafoundation.org)
    @date-created: 2010-08-16

    Generic Supply functionality such as catalogs and items that will be used across multiple modules
"""

module = "supply"

if deployment_settings.has_module("inv") or \
   deployment_settings.has_module("asset"):

    # Categories as component of Catalogs & Categories
    s3mgr.model.add_component("supply_item_category",
                              supply_catalog="catalog_id",
                              supply_item_category="parent_item_category_id")

    # Catalog Items as component of Items & Catalogs
    s3mgr.model.add_component("supply_catalog_item",
                              supply_item="item_id",
                              supply_catalog="catalog_id")

    # Packs as component of Items
    s3mgr.model.add_component("supply_item_pack",
                              supply_item="item_id")

    # Alternative Items as component of Items
    s3mgr.model.add_component("supply_item_alt",
                              supply_item="item_id")

    def supply_tables():
        """ Load the Supply Tables when needed """

        module = "supply"

        organisation_id = s3db.org_organisation_id
        organisation_represent = s3db.org_organisation_represent

        # =====================================================================
        # Brand
        #
        tablename = "supply_brand"
        table = db.define_table(tablename,
                                Field("name", length=128,
                                      notnull=True,
                                      unique=True),
                                s3_comments(),
                                *s3_meta_fields())

        # CRUD strings
        ADD_BRAND = T("Add Brand")
        LIST_BRAND = T("List Brands")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_BRAND,
            title_display = T("Brand Details"),
            title_list = LIST_BRAND,
            title_update = T("Edit Brand"),
            title_search = T("Search Brands"),
            subtitle_create = T("Add New Brand"),
            subtitle_list = T("Brands"),
            label_list_button = LIST_BRAND,
            label_create_button = ADD_BRAND,
            label_delete_button = T("Delete Brand"),
            msg_record_created = T("Brand added"),
            msg_record_modified = T("Brand updated"),
            msg_record_deleted = T("Brand deleted"),
            msg_list_empty = T("No Brands currently registered"))

        def supply_brand_represent(id):
            if not id:
                return NONE
            table = db.supply_brand
            query = (table.id == id)
            record = db(query).select(table.name,
                                      limitby=(0, 1)).first()
            if record:
                return record.name
            else:
                return UNKNOWN

        # Reusable Field
        brand_id = S3ReusableField("brand_id", db.supply_brand, sortby="name",
                    requires = IS_NULL_OR(IS_ONE_OF(db, "supply_brand.id",
                                                    "%(name)s",
                                                    sort=True)),
                    represent = supply_brand_represent,
                    label = T("Brand"),
                    comment = DIV(A(ADD_BRAND,
                                    _class="colorbox",
                                    _href=URL(c="supply", f="brand",
                                              args="create",
                                              vars=dict(format="popup")),
                                    _target="top",
                                    _title=ADD_BRAND),
                                  DIV( _class="tooltip",
                                       _title="%s|%s" % (T("Brand"),
                                                         T("The list of Brands are maintained by the Administrators.")))
                              ),
                    ondelete = "RESTRICT")

        # =====================================================================
        # Catalog (of Items)
        #
        tablename = "supply_catalog"
        table = db.define_table(tablename,
                                Field("name", length=128,
                                      notnull=True,
                                      unique=True),
                                organisation_id(),
                                s3_comments(),
                                *s3_meta_fields())

        # CRUD strings
        ADD_CATALOG = T("Add Catalog")
        LIST_CATALOG = T("List Catalogs")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_CATALOG,
            title_display = T("Catalog Details"),
            title_list = LIST_CATALOG,
            title_update = T("Edit Catalog"),
            title_search = T("Search Catalogs"),
            subtitle_create = T("Add New Catalog"),
            subtitle_list = T("Catalogs"),
            label_list_button = LIST_CATALOG,
            label_create_button = ADD_CATALOG,
            label_delete_button = T("Delete Catalog"),
            msg_record_created = T("Catalog added"),
            msg_record_modified = T("Catalog updated"),
            msg_record_deleted = T("Catalog deleted"),
            msg_list_empty = T("No Catalogs currently registered"))

        # Reusable Field
        catalog_id = S3ReusableField("catalog_id", db.supply_catalog,
                    sortby="name",
                    requires = IS_NULL_OR(IS_ONE_OF(db, "supply_catalog.id",
                                                    "%(name)s",
                                                    sort=True)),
                    represent = lambda id: \
                        s3_get_db_field_value(tablename = "supply_catalog",
                                              fieldname = "name",
                                              look_up_value = id) or NONE,
                    default = 1,
                    label = T("Catalog"),
                    comment = DIV(A(ADD_CATALOG,
                                    _class="colorbox",
                                    _href=URL(c="supply", f="catalog",
                                              args="create",
                                              vars=dict(format="popup")),
                                    _target="top",
                                    _title=ADD_CATALOG),
                                  DIV( _class="tooltip",
                                       _title="%s|%s" % (T("Catalog"),
                                                         T("The list of Catalogs are maintained by the Administrators.")))
                              ),
                    ondelete = "RESTRICT")

        # =====================================================================
        # Item Category
        #
        resourcename = "item_category"
        tablename = "supply_item_category"
        table = db.define_table(tablename,
                                catalog_id(),
                                #Field("level", "integer"),
                                Field("parent_item_category_id",
                                      "reference supply_item_category",
                                      label = T("Parent"),
                                      ondelete = "RESTRICT"),
                                Field("code", length=16),
                                Field("name", length=128,
                                      required = True),
                                Field("can_be_asset", "boolean",
                                      readable=deployment_settings.has_module("asset"),
                                      writable=deployment_settings.has_module("asset"),
                                      label=T("Items in Category can be Assets")),
                                Field("is_vehicle", "boolean",
                                      default=False,
                                      readable=deployment_settings.has_module("vehicle"),
                                      writable=deployment_settings.has_module("vehicle"),
                                      label=T("Items in Category are Vehicles")),
                                s3_comments(),
                                *s3_meta_fields())

        # CRUD strings
        ADD_ITEM_CATEGORY = T("Add Item Category")
        LIST_ITEM_CATEGORIES = T("List Item Categories")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_ITEM_CATEGORY,
            title_display = T("Item Category Details"),
            title_list = LIST_ITEM_CATEGORIES,
            title_update = T("Edit Item Category"),
            title_search = T("Search Item Categories"),
            subtitle_create = T("Add New Item Category"),
            subtitle_list = T("Item Categories"),
            label_list_button = LIST_ITEM_CATEGORIES,
            label_create_button = ADD_ITEM_CATEGORY,
            label_delete_button = T("Delete Item Category"),
            msg_record_created = T("Item Category added"),
            msg_record_modified = T("Item Category updated"),
            msg_record_deleted = T("Item Category deleted"),
            msg_list_empty = T("No Item Categories currently registered"))

        # Reusable Field
        item_category_requires = IS_NULL_OR(IS_ONE_OF(db,
                                                    "supply_item_category.id",
                                                    "%(name)s",
                                                    sort=True))

        def item_category_represent(id, use_code=True):
            """

            """
            if not id:
                return NONE
            table = db.supply_item_category

            represent = ""
            item_category_id = id
            while item_category_id:
                query = (table.id == item_category_id)
                r = db(query).select(table.code,
                                     table.name,
                                     table.parent_item_category_id,
                                     # left = table.on(table.id == table.parent_item_category_id), Doesn't work
                                     limitby=(0, 1),
                                     cache=(cache.ram, 60)).first()

                if r.code and use_code:
                    represent_append = r.code
                    represent_join = "-"
                else:
                    represent_append = r.name
                    represent_join = " - "

                if represent:
                    represent = represent_join.join([represent_append,
                                                     represent])
                else:
                    represent = represent_append
                item_category_id = r.parent_item_category_id

            return represent

        item_category_comment = DIV(A(ADD_ITEM_CATEGORY,
                                      _class="colorbox",
                                      _href=URL(c="supply", f="item_category",
                                                args="create",
                                                vars=dict(format="popup")),
                                      _target="top",
                                      _title=ADD_ITEM_CATEGORY),
                                    DIV( _class="tooltip",
                                         _title="%s|%s" % (T("Item Category"),
                                                           ADD_ITEM_CATEGORY)),
                                    )

        table.parent_item_category_id.requires = item_category_requires
        table.parent_item_category_id.represent = item_category_represent

        item_category_id = S3ReusableField("item_category_id",
                                           db.supply_item_category,
                                           sortby="name",
                                           requires=item_category_requires,
                                           represent=item_category_represent,
                                           label = T("Category"),
                                           comment = item_category_comment,
                                           ondelete = "RESTRICT")

        # =====================================================================
        # Item
        #
        #  These are Template items
        #  Instances of these become Inventory Items & Request items
        #
        tablename = "supply_item"
        table = db.define_table(
                    tablename,
                    Field("name",
                          required = True,
                          length=128, notnull=True),
                    Field("code",
                          length=16),
                    Field("um",
                          length=128,
                          label = T("Unit of Measure"),
                          notnull=True,
                          default = "piece"),
                    # Needed to auto-create a catalog_item
                    item_category_id("item_category_id",
                                     requires = IS_NULL_OR(IS_ONE_OF(db,
                                            "supply_item_category.id",
                                            "%(name)s",
                                            sort=True,
                                            filterby = "catalog_id",
                                            filter_opts = [1])
                                        )
                                    ),
                    brand_id(),
                    Field("model",
                          label = T("Model/Type"),
                          length=128),
                    Field("year",
                          "integer",
                          label = T("Year of Manufacture")),
                    Field("weight",
                          "double",
                          label = T("Weight (kg)"),
                          ),
                    Field("length",
                          "double",
                          label = T("Length (m)"),
                          ),
                    Field("width",
                          "double",
                          label = T("Width (m)"),
                          ),
                    Field("height",
                          "double",
                          label = T("Height (m)"),
                          ),
                    Field("volume",
                          "double",
                          label = T("Volume (m3)"),
                          ),
                    s3_comments(), # These comments do *not* pull through to an Inventory's Items or a Request's Items
                    *s3_meta_fields())

        # Categories in Progress
        #table.item_category_id_0.label = T("Category")
        #table.item_category_id_1.readable = table.item_category_id_1.writable = False
        #table.item_category_id_2.readable = table.item_category_id_2.writable = False

        # CRUD strings
        ADD_ITEM = T("Add Item")
        LIST_ITEMS = T("List Items")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_ITEM,
            title_display = T("Item Details"),
            title_list = LIST_ITEMS,
            title_update = T("Edit Item"),
            title_search = T("Search Items"),
            subtitle_create = T("Add New Item"),
            subtitle_list = T("Items"),
            label_list_button = LIST_ITEMS,
            label_create_button = ADD_ITEM,
            label_delete_button = T("Delete Item"),
            msg_record_created = T("Item added"),
            msg_record_modified = T("Item updated"),
            msg_record_deleted = T("Item deleted"),
            msg_list_empty = T("No Items currently registered"),
            msg_match = T("Matching Items"),
            msg_no_match = T("No Matching Items")
            )

        # ---------------------------------------------------------------------
        def supply_item_represent(id,
                                  # Needed for S3SearchAutocompleteWidget
                                  show_um = False,
                                  show_link = True,
                                  none_value = NONE):
            """ Representation of a supply_item """
            table = db.supply_item
            btable = db.supply_brand
            query = (table.id == id)
            r = db(query).select(table.name,
                                 table.model,
                                 table.um,
                                 btable.name,
                                 left = btable.on(table.brand_id == btable.id),
                                 limitby=(0, 1)).first()
            if not r:
                return none_value

            represent = [r.supply_item.name,
                         r.supply_brand.name,
                         r.supply_item.model]
            represent = [rep for rep in represent if rep]
            represent = " - ".join(represent)

            if show_um and r.supply_item.um:
                represent = "%s (%s)" % (represent, r.supply_item.um)

            local_request = request
            local_request.extension = "html"
            if show_link:
                return A(represent,
                         _href = URL( r = local_request,
                                      c = "supply",
                                      f = "item",
                                      args = [id]
                                     )
                         )
            else:
                return represent

        # ---------------------------------------------------------------------
        # Reusable Field
        supply_item_id = S3ReusableField("item_id", db.supply_item, sortby="name", # 'item_id' for backwards-compatibility
                    requires = IS_ONE_OF(db, "supply_item.id",
                                         supply_item_represent,
                                         sort=True),
                    represent = supply_item_represent,
                    label = T("Item"),
                    widget = S3SearchAutocompleteWidget(
                                    get_fieldname = "item_id",
                                    tablename = "supply_catalog_item",
                                    represent = lambda id: \
                                        supply_item_represent(id,
                                                              show_link=False,
                                                              # @ToDo: this doesn't work
                                                              show_um=False,
                                                              none_value=None),
                                    ),
                    comment = DIV(A(ADD_ITEM,
                                    _class="colorbox",
                                    _href=URL(c="supply", f="item",
                                              args="create",
                                              vars=dict(format="popup")),
                                    _target="top",
                                    _title=ADD_ITEM),
                              DIV( _class="tooltip",
                                   _title="%s|%s" % (T("Item"),
                                                     ADD_ITEM))),
                    ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        def resource_duplicate(tablename, job, fields=None):
            """
              This callback will be called when importing supply items it will look
              to see if the record being imported is a duplicate.

              @param tablename: The name of the table being imported into

              @param job: An S3ImportJob object which includes all the details
                          of the record being imported

              @param fields: The fields which to check for duplicates with.
                             If not passed, can be calculated - but inefficient

              If the record is a duplicate then it will set the job method to update

              Rules for finding a duplicate:
               - Look for a record with the same name, ignoring case
               - the same UM
               - and the same comments, if there are any

            """

            # ignore this processing if the id is set
            if job.id:
                return
            if job.tablename == tablename:
                table = job.table
                query = None
                if not fields:
                    fields = [field.name for field in db[tablename]
                              if field.writable and field.name != "id"]
                for field in fields:
                    value = field in job.data and job.data[field] or None
                    # Hack to get prepop working for Sahana Camp LA
                    if value:
                        try:
                            field_query = (table[field].lower() == value.lower())
                        except:
                            field_query = (table[field] == value)

#                    if not value:
#                        # Workaround
#                        if tablename == "supply_item_category" and field == "name":
#                            continue
#                        field_query = (table[field] == None)
#                    else:
#                        try:
#                            field_query = (table[field].lower() == value.lower())
#                        except:
#                            field_query = (table[field] == value)
                        if not query:
                            query = field_query
                        else:
                            query = query & field_query
                if query:
                    _duplicate = db(query).select(table.id,
                                                  limitby=(0, 1)).first()
                    if _duplicate:
                        job.id = _duplicate.id
                        job.method = job.METHOD.UPDATE

        # ---------------------------------------------------------------------
        def supply_item_onaccept(form):
            """
                Create a catalog_item for this item
                Update the UM (Unit of Measure) in the supply_item_pack table
            """
            item_id = form.vars.id

            if isinstance(form, SQLFORM):
            # Can't use auth.permission.format == "html" as it's still True for pre-populate via browser
                # Create a catalog_item for items added via browser
                table = db.supply_catalog_item

                #is request.vars the right place to store catalog_id?
                # no, it is not => imports won't have it and thus
                # imported items will always end up in the default
                # catalog
                catalog_id = request.vars.catalog_id
                ctable = db.supply_catalog
                if not catalog_id:
                    # Default Catalog
                    catalog = db().select(ctable.id,
                                          orderby=ctable.id,
                                          limitby=(0, 1)).first()
                    if catalog:
                        catalog_id = catalog.id
                    else:
                        # Create a default catalog
                        catalog_id = ctable.insert(name="Default Catalog")

                query = (table.item_id == item_id) & \
                        (table.deleted == False )
                if not db(query).count():
                    table.insert(catalog_id = catalog_id,
                                 item_category_id = form.vars.item_category_id,
                                 item_id = item_id,
                                 )

            # Update UM
            um = form.vars.um or db.supply_item.um.default
            table = db.supply_item_pack
            # Try to update the existing record
            query = (table.item_id == item_id) & \
                    (table.quantity == 1) & \
                    (table.deleted == False)
            if db(query).update(name = um) == 0:
                # Create a new item packet
                table.insert(item_id = item_id,
                             name = um,
                             quantity = 1)

        # ---------------------------------------------------------------------
        # Item Search Method
        #
        item_search = s3base.S3Search(
            advanced=(s3base.S3SearchSimpleWidget(
                        name="item_search_text",
                        label=T("Search"),
                        comment=T("Search for an item by its code, name, model and/or comment."),
                        field=["code",
                               "name",
                               "model",
                               #"item_category_id$name",
                               "comments" ]
                    ),
                      s3base.S3SearchOptionsWidget(
                        name="item_search_brand",
                        label=T("Brand"),
                        comment=T("Search for an item by brand."),
                        field=["brand_id"],
                        represent ="%(name)s",
                        cols = 3
                      ),
                      s3base.S3SearchOptionsWidget(
                        name="item_search_year",
                        label=T("Year"),
                        comment=T("Search for an item by Year of Manufacture."),
                        field=["year"],
                        #represent ="%(name)s",
                        cols = 1
                      ),
            )
        )

        s3mgr.configure(tablename,
                        onaccept = supply_item_onaccept,
                        search_method = item_search)

        # -----------------------------------------------------------------------------
        def supply_item_rheader(r):
            """ Resource Header for Items """

            if r.representation == "html":
                item = r.record
                if item:
                    tabs = [
                            (T("Edit Details"), None),
                            (T("Packs"), "item_pack"),
                            (T("Alternative Items"), "item_alt"),
                            (T("In Inventories"), "inv_item"),
                           ]
                    if deployment_settings.has_module("req"):
                        tabs.append((T("Requested"), "req_item"))
                    tabs.append((T("In Catalogs"), "catalog_item"))
                    rheader_tabs = s3_rheader_tabs(r, tabs)
                    #table = db.supply_item_category
                    #query = (table.id == item.item_category_id_0)
                    #category = db(query).select(table.name,
                    #                            limitby=(0, 1)).first()
                    #if category:
                    #    category = category.name
                    #else:
                    #    category = NONE
                    rheader = DIV(TABLE(TR( TH("%s: " % T("Name")), item.name,
                                          ),
                                        TR( TH("%s: " % T("Brand")),
                                            response.s3.supply_brand_represent(item.brand_id),
                                          ),
                                        TR( TH("%s: " % T("Model/Type")), item.model or NONE,
                                          ),
                                       ),
                                  rheader_tabs
                                 )
                    return rheader
            return None

        # ---------------------------------------------------------------------
        def supply_item_controller():
            """ RESTful CRUD controller """

            # Load models for components
            # Can't be done in prep, because the resource (& components) will
            # already be defined then
            if "req_item" in request.args:
                s3mgr.load("req_req_item") # Also loads Inv
            elif "inv_item" in request.args:
                s3mgr.load("inv_inv_item")

            return s3_rest_controller("supply", "item",
                                      rheader=supply_item_rheader)

        # =====================================================================
        # Catalog Item
        #
        # This resource is used to link Items with Catalogs (n-to-n)
        # Item Categories will also be catalog specific
        #
        resourcename = "catalog_item"
        tablename = "supply_catalog_item"
        table = db.define_table(tablename,
                                catalog_id(),
                                item_category_id("item_category_id",
                                                 #label = T("Group"),

                                                 # Filters item_category_id based on catalog_id
                                                 script =
    SCRIPT("""
    $(document).ready(function() {
        S3FilterFieldChange({
            'FilterField':   'catalog_id',
            'Field':         'item_category_id',
            'FieldPrefix':   'supply',
            'FieldResource': 'item_category',
        });
    });"""),
                                                 ),
                                supply_item_id(script = None), # No Item Pack Filter
                                s3_comments(), # These comments do *not* pull through to an Inventory's Items or a Request's Items
                                *s3_meta_fields())

        # CRUD strings
        ADD_ITEM = T("Add Catalog Item")
        LIST_ITEMS = T("List Catalog Items")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_ITEM,
            title_display = T("Item Catalog Details"),
            title_list = LIST_ITEMS,
            title_update = T("Edit Catalog Item"),
            title_search = T("Search Catalog Items"),
            subtitle_create = T("Add Item to Catalog"),
            subtitle_list = T("Catalog Items"),
            label_list_button = LIST_ITEMS,
            label_create_button = ADD_ITEM,
            label_delete_button = T("Delete Catalog Item"),
            msg_record_created = T("Catalog Item added"),
            msg_record_modified = T("Catalog Item updated"),
            msg_record_deleted = T("Catalog Item deleted"),
            msg_list_empty = T("No Catalog Items currently registered"),
            msg_match = T("Matching Catalog Items"),
            msg_no_match = T("No Matching Catalog Items")
            )

        def catalog_item_represent(id):
            """
                @todo:
            """
            table = db.supply_item
            query = (table.id == id)
            r = db(query).select(table.name,
                                 table.um,
                                 limitby=(0, 1)).first()
            if not r:
                return NONE
            elif not r.um:
                return r.name
            else:
                return "%s (%s)" % (r.name, r.um)

        # ---------------------------------------------------------------------
        # Catalog Item Search Method
        #

        def catalog_item_search_simple_widget(type):
            return s3base.S3SearchSimpleWidget(
                name="catalog_item_search_simple_%s" % type,
                label=T("Search"),
                comment= T("Search for an item by its code, name, model and/or comment."),
                field=[#"comments", # Causes a major Join which kills servers
                       #"item_category_id$code", #These lines are causing issues...very slow - perhaps broken
                       #"item_category_id$name",
                       #"item_id$brand_id$name",
                       #"item_category_id$parent_item_category_id$code"
                       #"item_category_id$parent_item_category_id$name"
                       "item_id$code",
                       "item_id$name",
                       "item_id$model",
                       "item_id$comments"
                       ],
                )

        catalog_item_search = s3base.S3Search(
            simple=( catalog_item_search_simple_widget("simple") ),
            advanced=( catalog_item_search_simple_widget("advanced"),
                       s3base.S3SearchOptionsWidget(
                         name="catalog_item_search_catalog",
                         label=T("Catalog"),
                         comment=T("Search for an item by catalog."),
                         field=["catalog_id"],
                         represent ="%(name)s",
                         cols = 3
                       ),
                       s3base.S3SearchOptionsWidget(
                         name="catalog_item_search_category",
                         label=T("Category"),
                         comment=T("Search for an item by category."),
                         field=["item_category_id"],
                         represent = lambda id: \
                            item_category_represent(id, use_code=False),
                         cols = 3
                       ),
                       s3base.S3SearchOptionsWidget(
                         name="catalog_item_search_brand",
                         label=T("Brand"),
                         comment=T("Search for an item by brand."),
                         field=["item_id$brand_id"],
                         represent ="%(name)s",
                         cols = 3
                       ),
            )
        )

        s3mgr.configure(tablename,
                        search_method = catalog_item_search)

        # ---------------------------------------------------------------------
        # @ToDo: Put the most common patterns at the top to optimise
        um_patterns = ["\sper\s?(.*)$",                         # CHOCOLATE, per 100g
                       #"\((.*)\)$",                            # OUTWARD REGISTER for shipping (50 sheets)
                       "([0-9]+\s?(gramm?e?s?|L|g|kg))$",       # Navarin de mouton 285 grammes
                       ",\s(kit|pair|btl|bottle|tab|vial)\.?$", # STAMP, IFRC, Englishlue, btl.
                       "\s(bottle)\.?$",                        # MINERAL WATER, 1.5L bottle
                       ",\s((bag|box|kit) of .*)\.?$",          # (bag, diplomatic) LEAD SEAL, bag of 100
                       ]

        def item_um_from_name(name,um):
            import re
            if not um:
                for um_pattern in um_patterns:
                    m = re.search(um_pattern,name)
                    if m:
                        um = m.group(1).strip()
                        # Rename um from name
                        name = re.sub(um_pattern, "", name)
                        # Remove trailing , & wh sp
                        name = re.sub("(,)$", "", name).strip()
                        return dict(name = name,
                                    um = um)
            return {}
        # ---------------------------------------------------------------------
        # Calculate once, instead of for each record
        item_duplicate_fields = {}
        for tablename in ["supply_item", "supply_catalog_item"]:
            item_duplicate_fields[tablename] = [field.name for field in db[tablename]
                                                if field.writable and
                                                field.name != "id"]

        def item_duplicate(job):
            """
                Callback function used to look for duplicates during
                the import process
            """

            tablename = job.tablename
            resource_duplicate = response.s3.resource_duplicate

            if tablename == "supply_item":
                job.data.update(item_um_from_name(job.data.name,
                                                  job.data.um)
                                )

            if tablename in ["supply_item", "supply_catalog_item"]:
                resource_duplicate(tablename, job,
                                   item_duplicate_fields[tablename])

            elif tablename == "supply_item_category":
                resource_duplicate("supply_item_category", job,
                                   fields = ["catalog_id",
                                             "parent_item_category_id",
                                             "code",
                                             "name"])

        s3mgr.configure("supply_item", deduplicate=item_duplicate)
        s3mgr.configure("supply_catalog_item", deduplicate=item_duplicate)
        s3mgr.configure("supply_item_category", deduplicate=item_duplicate)

        # =====================================================================
        # Item Pack
        #
        #  Items can be distributed in different containers
        #
        resourcename = "item_pack"
        tablename = "supply_item_pack"
        table = db.define_table(tablename,
                                supply_item_id(empty=False),
                                Field("name", length=128,
                                      default = T("piece"),
                                      notnull=True), # Ideally this would reference another table for normalising Pack names
                                Field("quantity", "double", notnull=True),
                                s3_comments(),
                                *s3_meta_fields())

        # CRUD strings
        ADD_ITEM_PACK = T("Add Item Pack")
        LIST_ITEM_PACK = T("List Item Packs")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_ITEM_PACK,
            title_display = T("Item Pack Details"),
            title_list = LIST_ITEM_PACK,
            title_update = T("Edit Item Pack"),
            title_search = T("Search Item Packs"),
            subtitle_create = T("Add New Item Pack"),
            subtitle_list = T("Item Packs"),
            label_list_button = LIST_ITEM_PACK,
            label_create_button = ADD_ITEM_PACK,
            label_delete_button = T("Delete Item Pack"),
            msg_record_created = T("Item Pack added"),
            msg_record_modified = T("Item Pack updated"),
            msg_record_deleted = T("Item Pack deleted"),
            msg_list_empty = T("No Item Packs currently registered"))

        # ---------------------------------------------------------------------
        def item_pack_represent(id):
            table = db.supply_item_pack
            query = (table.id == id) & \
                    (table.item_id == db.supply_item.id)
            record = db(query).select(table.name,
                                      table.quantity,
                                      db.supply_item.um,
                                      limitby = (0, 1)).first()
            if record:
                if record.supply_item_pack.quantity == 1:
                    return record.supply_item_pack.name
                else:
                    return "%s (%s x %s)" % (record.supply_item_pack.name,
                                             record.supply_item_pack.quantity,
                                             record.supply_item.um)
            else:
                return NONE

        # ---------------------------------------------------------------------
        # Reusable Field
        item_pack_id = S3ReusableField("item_pack_id", db.supply_item_pack,
                    sortby="name",
                    # Do not display any packs initially
                    # will be populated by S3FilterFieldChange
                    requires = IS_ONE_OF_EMPTY_SELECT(db,
                                         "supply_item_pack.id",
                                         item_pack_represent,
                                         sort=True,
                                         # @ToDo: Enforce "Required" for imports
                                         # @ToDo: Populate based on item_id in controller instead of IS_ONE_OF_EMPTY_SELECT
                                         # filterby = "item_id",
                                         # filter_opts = [....],
                                         ),
                    represent = item_pack_represent,
                    label = T("Pack"),
                    comment = DIV(DIV( _class="tooltip",
                                       _title="%s|%s" % (T("Item Packs"),
                                                         T("The way in which an item is normally distributed"))),
                                  A( ADD_ITEM_PACK,
                                     _class="colorbox",
                                     _href=URL(c="supply", f="item_pack",
                                               args="create",
                                               vars=dict(format="popup")
                                               ),
                                     _target="top",
                                     _id = "item_pack_add",
                                     _style = "display: none",
                                     ),
                                  ),
                    script = SCRIPT(
"""
S3FilterFieldChange({
    'FilterField':    'item_id',
    'Field':        'item_pack_id',
    'FieldResource':'item_pack',
    'FieldPrefix':    'supply',
    'msgNoRecords':    S3.i18n.no_packs,
    'fncPrep':        fncPrepItem,
    'fncRepresent':    fncRepresentItem
});"""),
                    ondelete = "RESTRICT")

        #def record_pack_quantity(r):
        #    item_pack_id = r.get("item_pack_id", None)
        #    if item_pack_id:
        #        return s3_get_db_field_value(tablename = "supply_item_pack",
        #                                     fieldname = "quantity",
        #                                     look_up_value = item_pack_id)
        #    else:
        #        return None

        # ---------------------------------------------------------------------
        # Virtual Field for pack_quantity
        class item_pack_virtualfields(dict, object):
            def __init__(self,
                         tablename):
                self.tablename = tablename
            def pack_quantity(self):
                if self.tablename == "inv_inv_item":
                    item_pack = self.inv_inv_item.item_pack_id
                elif self.tablename == "req_req_item":
                    item_pack = self.req_req_item.item_pack_id
                elif self.tablename == "req_commit_item":
                    item_pack = self.req_commit_item.item_pack_id
                elif self.tablename == "inv_recv_item":
                    item_pack = self.inv_recv_item.item_pack_id
                elif self.tablename == "inv_send_item":
                    item_pack = self.inv_send_item.item_pack_id
                else:
                    item_pack = None
                if item_pack:
                    return item_pack.quantity
                else:
                    return None

        # ---------------------------------------------------------------------
        def item_pack_duplicate(job):
            """
                Callback function used to look for duplicates during
                the import process
            """

            tablename = job.tablename
            resource_duplicate = response.s3.resource_duplicate
            # An Item Pack is a duplicate if both the Name & Item are identical
            resource_duplicate(tablename, job,
                               fields = ["name",
                                         "item_id",
                                        ])

        s3mgr.configure("supply_item_pack", deduplicate=item_pack_duplicate)

        # =====================================================================
        # Alternative Items
        #
        #  If the desired item isn't found, then these are designated as
        #  suitable alternatives
        #
        resourcename = "item_alt"
        tablename = "supply_item_alt"
        table = db.define_table(tablename,
                                supply_item_id(notnull=True),
                                Field("quantity",
                                      "double",
                                      comment = DIV( _class = "tooltip",
                                                     _title = "%s|%s" %
                                                             (T("Quantity"),
                                                              T("The number of Units of Measure of the Alternative Items which is equal to One Unit of Measure of the Item")
                                                              )
                                                    ),
                                      default = 1,
                                      notnull=True),
                                supply_item_id("alt_item_id",
                                               notnull=True),
                                s3_comments(),
                                *s3_meta_fields())

        # CRUD strings
        ADD_ALT_ITEM = T("Add Alternative Item")
        LIST_ALT_ITEM = T("List Alternative Items")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_ALT_ITEM,
            title_display = T("Alternative Item Details"),
            title_list = LIST_ALT_ITEM,
            title_update = T("Edit Alternative Item"),
            title_search = T("Search Alternative Items"),
            subtitle_create = T("Add New Alternative Item"),
            subtitle_list = T("Alternative Items"),
            label_list_button = LIST_ALT_ITEM,
            label_create_button = ADD_ALT_ITEM,
            label_delete_button = T("Delete Alternative Item"),
            msg_record_created = T("Alternative Item added"),
            msg_record_modified = T("Alternative Item updated"),
            msg_record_deleted = T("Alternative Item deleted"),
            msg_list_empty = T("No Alternative Items currently registered"))

        #def item_alt_represent(id):
        #    try:
        #        return supply_item_represent(db.supply_item_alt[id].item_id)
        #    except:
        #        return NONE

        # Reusable Field - probably not needed
        #item_alt_id = S3ReusableField("item_alt_id", db.supply_item_alt,
        #            sortby="name",
        #            requires = IS_NULL_OR(IS_ONE_OF(db,
        #                                            "supply_item_alt.id",
        #                                            item_alt_represent,
        #                                            sort=True)),
        #            represent = item_alt_represent,
        #            label = T("Alternative Item"),
        #            comment = DIV(DIV( _class="tooltip",
        #                               _title="%s|%s" % (T("Alternative Item"),
        #                                                 T("An item which can be used in place of another item"))),
        #                          A( ADD_ALT_ITEM,
        #                             _class="colorbox",
        #                             _href=URL(#                                       c="supply",
        #                                       f="item_alt",
        #                                       args="create",
        #                                       vars=dict(format="popup")
        #                                       ),
        #                             _target="top",
        #                             _id = "item_alt_add",
        #                             _style = "display: none",
        #                             ),
        #                          ),
        #            ondelete = "RESTRICT")

        # =====================================================================
        def supply_item_add (quantity_1, pack_quantity_1,
                             quantity_2, pack_quantity_2):
            """
                Adds item quantities together, accounting for different pack
                quantities.
                Returned quantity according to pack_quantity_1
            """
            if pack_quantity_1 == pack_quantity_2:
                # Faster calculation
                return quantity_1 + quantity_2
            else:
                return ((quantity_1 * pack_quantity_1) +
                        (quantity_2 * pack_quantity_2)) / pack_quantity_1

        # =============================================================================
        # Item Super-Entity
        #
        # This super entity provides a common way to provide a foreign key to supply_item
        # - it allows searching/reporting across Item types easily.
        #
        item_types = Storage(
                            inv_inv_item = T("Inventory Item"),
                            inv_recv_item = T("Order Item"),
                            proc_plan_item = T("Planned Procurement Item"),
                            )

        tablename = "supply_item_entity"
        table = super_entity(tablename, "item_entity_id", item_types,
                             # @ToDo: Make Items Trackable?
                             #super_link("track_id", "sit_trackable"),
                             #location_id(),
                             supply_item_id(represent = lambda id: \
                                                supply_item_represent(id,
                                                                      show_um = False,
                                                                      show_link = True)),
                             item_pack_id(),
                             Field("quantity", "double",
                                   label = T("Quantity"),
                                   default = 1.0,
                                   notnull = True),
                             *s3_ownerstamp())

        # -----------------------------------------------------------------------------
        def item_represent(id):
            """
                Represent an item entity in option fields or list views
                - unused, we use VirtualField instead
            """

            item_str = NONE
            item_table = db.supply_item_entity

            if not id:
                return item_str

            if isinstance(id, Row) and "instance_type" in id:
                # Do not repeat the lookup if already done by IS_ONE_OF
                item = id
            else:
                item = db(item_table._id == id).select(item_table.instance_type,
                                                       limitby=(0, 1)).first()
                if not item:
                    return item_str

            instance_type = item.instance_type

            if instance_type == "inv_inv_item":
                item_str = T("In Stock")
            elif instance_type == "inv_recv_item":
                s3mgr.load(instance_type)
                itable = db[instance_type]
                rtable = db.inv_recv
                query = (itable.item_entity_id == id) & \
                        (rtable.id == itable.recv_id)
                eta = db(query).select(rtable.eta,
                                       limitby=(0, 1)).first().eta
                item_str = T("Due %(date)s") % dict(date=eta)

            return item_str

        # -----------------------------------------------------------------------------
        item_id = super_link("item_entity_id", "supply_item_entity",
                             #writable = True,
                             #readable = True,
                             #label = T("Status"),
                             #represent = item_represent,
                             # Comment these to use a Dropdown & not an Autocomplete
                             #widget = S3ItemAutocompleteWidget(),
                             #comment = DIV(_class="tooltip",
                             #              _title="%s|%s" % (T("Item"),
                             #                                T("Enter some characters to bring up a list of possible matches")))
                            )

        # ---------------------------------------------------------------------
        # Item Search Method
        #
        item_entity_search = s3base.S3Search(
            # Advanced Search only
            advanced=(s3base.S3SearchSimpleWidget(
                        name="item_entity_search_text",
                        label=T("Search"),
                        comment=T("Search for an item by text."),
                        field=[ "item_id$name",
                                #"item_id$item_category_id$name",
                                #"site_id$name"
                                ]
                      ),
                      s3base.S3SearchOptionsWidget(
                        name="item_entity_search_category",
                        label=T("Code Share"),
                        field=["item_id$item_category_id"],
                        represent ="%(name)s",
                        comment=T("If none are selected, then all are searched."),
                        cols = 2
                      ),
                      #s3base.S3SearchOptionsWidget(
                      #  name="item_entity_search_country",
                      #  label=T("Country"),
                      #  field=["country"],
                      #  represent ="%(name)s",
                      #  comment=T("If none are selected, then all are searched."),
                      #  cols = 2
                      #),
            ))

        # ---------------------------------------------------------------------
        s3mgr.configure(tablename,
                        search_method = item_entity_search)

        # ---------------------------------------------------------------------
        def item_entity_controller():
            """
                RESTful CRUD controller
                - consolidated report of inv_item, recv_item & proc_plan_item
            """

            # Load Models
            s3mgr.load("supply_item_entity")
            if deployment_settings.has_module("inv"):
                s3mgr.load("inv_recv_item")
            if deployment_settings.has_module("proc"):
                s3mgr.load("proc_plan_item")

            tablename = "supply_item_entity"
            table = db[tablename]
            # CRUD strings
            s3.crud_strings[tablename] = Storage(
                title_create = T("Add Item"),
                title_display = T("Item Details"),
                title_list = T("List Items"),
                title_update = T("Edit Item"),
                title_search = T("Search Items"),
                subtitle_create = T("Add New Item"),
                subtitle_list = T("Items"),
                label_list_button = T("List Items"),
                label_create_button = T("Add Item"),
                label_delete_button = T("Delete Item"),
                msg_record_created = T("Item added"),
                msg_record_modified = T("Item updated"),
                msg_record_deleted = T("Item deleted"),
                msg_list_empty = T("No Items currently registered"))

            # -------------------------------------------------------------------------
            # Virtual Fields for category, country, organisation & status
            class item_entity_virtualfields:
                # Fields to be loaded by sqltable as qfields
                # without them being list_fields
                # (These cannot contain VirtualFields)
                # In this case we just load it once to save a query in each method
                extra_fields = [
                            "instance_type"
                        ]

                def category(self):
                    category = NONE
                    table = db.supply_item
                    try:
                        query = (table.id == self.supply_item_entity.item_id)
                    except:
                             # We are being instantiated inside one of the other methods
                            return None
                    record = db(query).select(table.item_category_id,
                                              limitby=(0, 1)).first()
                    if record:
                        category = response.s3.item_category_represent(record.item_category_id)
                    return category

                def country(self):
                    country = NONE
                    etable = db.supply_item_entity
                    instance_type = self.supply_item_entity.instance_type
                    if instance_type == "inv_inv_item":
                        tablename = instance_type
                        s3mgr.load(instance_type)
                        itable = db[instance_type]
                        otable = db.org_office
                        try:
                            query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                                    (otable.site_id == itable.site_id)
                        except:
                             # We are being instantiated inside one of the other methods
                            return None
                        record = db(query).select(otable.L0,
                                                  limitby=(0, 1)).first()
                        if record:
                            country = record.L0 or T("Unknown")
                    elif instance_type == "inv_recv_item":
                        tablename = instance_type
                        s3mgr.load(instance_type)
                        itable = db[instance_type]
                        rtable = db.inv_recv
                        otable = db.org_office
                        try:
                            query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                                    (rtable.id == itable.recv_id) & \
                                    (otable.site_id == rtable.site_id)
                        except:
                             # We are being instantiated inside one of the other methods
                            return None
                        record = db(query).select(otable.L0,
                                                  limitby=(0, 1)).first()
                        if record:
                            country = record.L0 or T("Unknown")
                    elif instance_type == "proc_plan_item":
                        tablename = instance_type
                        s3mgr.load(instance_type)
                        itable = db[instance_type]
                        ptable = db.proc_plan
                        otable = db.org_office
                        try:
                            query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                                    (ptable.id == itable.plan_id) & \
                                    (otable.site_id == ptable.site_id)
                        except:
                             # We are being instantiated inside one of the other methods
                            return None
                        record = db(query).select(otable.L0,
                                                  limitby=(0, 1)).first()
                        if record:
                            country = record.L0 or T("Unknown")
                    else:
                        # @ToDo: Assets and req_items
                        return NONE
                    return country

                def organisation(self):
                    organisation = NONE
                    etable = db.supply_item_entity
                    instance_type = self.supply_item_entity.instance_type
                    if instance_type == "inv_inv_item":
                        tablename = instance_type
                        s3mgr.load(instance_type)
                        itable = db[instance_type]
                        otable = db.org_office
                        try:
                            query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                                    (otable.site_id == itable.site_id)
                        except:
                             # We are being instantiated inside one of the other methods
                            return None
                        record = db(query).select(otable.organisation_id,
                                                  limitby=(0, 1)).first()
                        if record:
                            organisation = organisation_represent(record.organisation_id,
                                                                  acronym=False)
                    elif instance_type == "proc_plan_item":
                        tablename = instance_type
                        s3mgr.load(instance_type)
                        itable = db[instance_type]
                        rtable = db.proc_plan
                        otable = db.org_office
                        try:
                            query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                                    (rtable.id == itable.plan_id) & \
                                    (otable.site_id == rtable.site_id)
                        except:
                             # We are being instantiated inside one of the other methods
                            return None
                        record = db(query).select(otable.organisation_id,
                                                  limitby=(0, 1)).first()
                        if record:
                            organisation = organisation_represent(record.organisation_id,
                                                                  acronym=False)
                    elif instance_type == "inv_recv_item":
                        tablename = instance_type
                        s3mgr.load(instance_type)
                        itable = db[instance_type]
                        rtable = db.inv_recv
                        otable = db.org_office
                        try:
                            query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                                    (rtable.id == itable.recv_id) & \
                                    (otable.site_id == rtable.site_id)
                        except:
                             # We are being instantiated inside one of the other methods
                            return None
                        record = db(query).select(otable.organisation_id,
                                                  limitby=(0, 1)).first()
                        if record:
                            organisation = organisation_represent(record.organisation_id,
                                                                  acronym=False)
                    else:
                        # @ToDo: Assets and req_items
                        return NONE
                    return organisation

                #def site(self):
                def contacts(self):
                    site = NONE
                    etable = db.supply_item_entity
                    instance_type = self.supply_item_entity.instance_type
                    if instance_type == "inv_inv_item":
                        tablename = instance_type
                        s3mgr.load(instance_type)
                        itable = db[instance_type]
                        try:
                            query = (itable.item_entity_id == self.supply_item_entity[etable._id.name])
                        except:
                             # We are being instantiated inside one of the other methods
                            return None
                        record = db(query).select(itable.site_id,
                                                  limitby=(0, 1)).first()
                    elif instance_type == "inv_recv_item":
                        tablename = instance_type
                        s3mgr.load(instance_type)
                        itable = db[instance_type]
                        rtable = db.inv_recv
                        try:
                            query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                                    (rtable.id == itable.recv_id)
                        except:
                             # We are being instantiated inside one of the other methods
                            return None
                        record = db(query).select(rtable.site_id,
                                                  limitby=(0, 1)).first()
                    elif instance_type == "proc_plan_item":
                        tablename = instance_type
                        s3mgr.load(instance_type)
                        itable = db[instance_type]
                        ptable = db.proc_plan
                        try:
                            query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                                    (ptable.id == itable.plan_id)
                        except:
                             # We are being instantiated inside one of the other methods
                            return None
                        record = db(query).select(ptable.site_id,
                                                  limitby=(0, 1)).first()
                    else:
                        # @ToDo: Assets and req_items
                        return NONE

                    #site = s3db.org_site_represent(record.site_id)
                    #return site
                    otable = db.org_office
                    record = db(otable.site_id == record.site_id).select(otable.id,
                                                                         otable.comments,
                                                                         limitby=(0, 1)).first()
                    if request.extension == "xls" or \
                       request.extension == "pdf":
                        if record.comments:
                            return record.comments
                        else:
                            return NONE
                    elif record.comments:
                        comments = comments_represent(record.comments, showlink=False)
                    else:
                        comments = NONE
                    return A(comments,
                             _href = URL(f="office",
                                         args = [record.id]))

                def status(self):
                    status = NONE
                    etable = db.supply_item_entity
                    instance_type = self.supply_item_entity.instance_type
                    if instance_type == "inv_inv_item":
                        tablename = instance_type
                        s3mgr.load(instance_type)
                        itable = db[instance_type]
                        try:
                            query = (itable.item_entity_id == self.supply_item_entity[etable._id.name])
                        except:
                            # We are being instantiated inside one of the other methods
                            return None
                        record = db(query).select(itable.expiry_date,
                                                  limitby=(0, 1)).first()
                        if record:
                            if record.expiry_date:
                                status = T("Stock Expires %(date)s") % dict(date=record.expiry_date)
                            else:
                               status = T("In Stock")
                    elif instance_type == "proc_plan_item":
                        tablename = instance_type
                        s3mgr.load(instance_type)
                        itable = db[instance_type]
                        rtable = db.proc_plan
                        try:
                            query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                                    (rtable.id == itable.plan_id)
                        except:
                            # We are being instantiated inside one of the other methods
                            return None
                        record = db(query).select(rtable.eta,
                                                  limitby=(0, 1)).first()
                        if record:
                            if record.eta:
                                status = T("Planned %(date)s") % dict(date=record.eta)
                            else:
                               status = T("Planned Procurement")
                    elif instance_type == "inv_recv_item":
                        tablename = instance_type
                        s3mgr.load(instance_type)
                        itable = db[instance_type]
                        rtable = db.inv_recv
                        try:
                            query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                                    (rtable.id == itable.recv_id)
                        except:
                            # We are being instantiated inside one of the other methods
                            return None
                        record = db(query).select(rtable.eta,
                                                  limitby=(0, 1)).first()
                        if record:
                            if record.eta:
                                status = T("Order Due %(date)s") % dict(date=record.eta)
                            else:
                                status = T("On Order")
                    else:
                        # @ToDo: Assets and req_items
                        return NONE
                    return status

            table.virtualfields.append(item_entity_virtualfields())

            # Allow VirtualFields to be sortable/searchable
            response.s3.no_sspag = True

            s3mgr.configure(tablename,
                            deletable = False,
                            insertable = False,
                            # @ToDo: Allow VirtualFields to be used to Group Reports
                            #report_groupby = "category",
                            list_fields = [(T("Category"), "category"),
                                           "item_id",
                                           "quantity",
                                           (T("Unit of Measure"), "item_pack_id"),
                                           (T("Status"), "status"),
                                           (T("Country"), "country"),
                                           (T("Organization"), "organisation"),
                                           #(T("Office"), "site"),
                                           (T("Contacts"), "contacts"),
                                        ])

            def postp(r, output):
                if r.interactive and not r.record:
                    # Provide some manual Filters above the list
                    rheader = DIV()

                    # Filter by Category
                    table = db.supply_item_category
                    etable = db.supply_item_entity
                    itable = db.supply_item
                    query = (etable.deleted == False) & \
                            (etable.item_id == itable.id) & \
                            (itable.item_category_id == table.id)
                    categories = db(query).select(table.id,
                                                  table.name,
                                                  distinct=True)
                    select = SELECT(_multiple="multiple", _id="category_dropdown")
                    for category in categories:
                        select.append(OPTION(category.name, _name=category.id))
                    rheader.append(DIV(B("%s:" % T("Filter by Category")),
                                       BR(),
                                       select,
                                       _class="rfilter"))

                    # Filter by Status
                    select = SELECT(_multiple="multiple", _id="status_dropdown")
                    if deployment_settings.has_module("inv"):
                        select.append(OPTION(T("In Stock")))
                        select.append(OPTION(T("On Order")))
                    if deployment_settings.has_module("proc"):
                        select.append(OPTION(T("Planned Procurement")))
                    rheader.append(DIV(B("%s:" % T("Filter by Status")),
                                       BR(),
                                       select,
                                       _class="rfilter"))

                    output.update(rheader=rheader)
                    output.pop("subtitle")

                    # Find Offices with Items
                    # @ToDo: Other Site types (how to do this as a big Join?)
                    table = db.org_office
                    otable = db.org_organisation
                    fields = [table.L0,
                              #table.name,
                              otable.name]
                    query = (table.deleted == False) & \
                            (table.organisation_id == otable.id)
                    isites = []
                    rsites = []
                    psites = []
                    # @ToDo: Assets & Req_Items
                    # @ToDo: Try to do this as a Join?
                    if deployment_settings.has_module("inv"):
                        iquery = query & (db.inv_inv_item.site_id == table.site_id)
                        isites = db(iquery).select(distinct=True,
                                                   *fields)
                        rquery = query & (db.inv_recv_item.recv_id == db.inv_recv.id) & \
                                         (db.inv_recv.site_id == table.site_id)
                        rsites = db(rquery).select(distinct=True,
                                                   *fields)
                    if deployment_settings.has_module("proc"):
                        pquery = query & (db.proc_plan_item.plan_id == db.proc_plan.id) & \
                                         (db.proc_plan.site_id == table.site_id)
                        psites = db(pquery).select(distinct=True,
                                                   *fields)
                    sites = []
                    for site in isites:
                        if site not in sites:
                            sites.append(site)
                    for site in rsites:
                        if site not in sites:
                            sites.append(site)
                    for site in psites:
                        if site not in sites:
                            sites.append(site)

                    # Filter by Country
                    select = SELECT(_multiple="multiple", _id="country_dropdown")
                    countries = []
                    for site in sites:
                        country = site.org_office.L0
                        if country not in countries:
                            select.append(OPTION(country or T("Unknown")))
                            countries.append(country)
                    rheader.append(DIV(B("%s:" % T("Filter by Country")),
                                       BR(),
                                       select,
                                       _class="rfilter"))

                    # Filter by Organisation
                    select = SELECT(_multiple="multiple", _id="organisation_dropdown")
                    orgs = []
                    for site in sites:
                        org = site.org_organisation.name
                        if org not in orgs:
                            select.append(OPTION(org or T("Unknown")))
                            orgs.append(org)
                    rheader.append(DIV(B("%s:" % T("Filter by Organization")),
                                       BR(),
                                       select,
                                       _class="rfilter"))

                    # http://datatables.net/api#fnFilter
                    # Columns:
                    #  1 = Category
                    #  5 = Status (@ToDo: Assets & Req Items)
                    #  6 = Country
                    #  7 = Organisation
                    # Clear column filter before applying new one
                    #
                    # @ToDo: Hide options which are no longer relevant because
                    #        of the other filters applied
                    #
                    response.s3.jquery_ready.append("""
function filterColumns() {
    var oTable = $('#list').dataTable();
    var values = '';
    $('#category_dropdown option:selected').each(function () {
        values += $(this).text() + '|';
    });
    var regex = (values == '' ?  '': '^' + values.slice(0, -1) + '$');
    oTable.fnFilter('', 1, false);
    oTable.fnFilter( regex, 1, true, false );
    values = '';
    $('#status_dropdown option:selected').each(function () {
        if ($(this).text() == '""" + T("On Order") + """') {
            values += $(this).text() + '|' + '""" + T("Order") + """.*' + '|';
        } else if ($(this).text() == '""" + T("Planned Procurement") + """') {
            values += '""" + T("Planned") + """.*' + '|';
        } else {
            values += $(this).text() + '|' + '""" + T("Stock") + """.*' + '|';
        }
    });
    var regex = (values == '' ?  '': '^' + values.slice(0, -1) + '$');
    oTable.fnFilter('', 5, false);
    oTable.fnFilter( regex, 5, true, false );
    values = '';
    $('#country_dropdown option:selected').each(function () {
        values += $(this).text() + '|';
    });
    var regex = (values == '' ?  '': '^' + values.slice(0, -1) + '$');
    oTable.fnFilter('', 6, false);
    oTable.fnFilter( regex, 6, true, false );
    values = '';
    $('#organisation_dropdown option:selected').each(function () {
        values += $(this).text() + '|';
    });
    var regex = (values == '' ?  '': '^' + values.slice(0, -1) + '$');
    oTable.fnFilter('', 7, false);
    oTable.fnFilter( regex, 7, true, false );
}
$('#category_dropdown').change(function () {
    filterColumns();
    var values = [];
    $('#category_dropdown option:selected').each(function () {
        values.push( $(this).attr('name') );
    });
    if ( values.length ) {
        $('#list_formats a').attr('href', function() {
            var href = this.href.split('?')[0] + '?item_entity.item_id$item_category_id=' + values[0];
            for ( i = 1; i <= (values.length - 1); i++ ) {
                href = href + ',' + values[i]
            }
            return href;
        });
    } else {
        $('#list_formats a').attr('href', function() {
            return this.href.split('?')[0];
        });
    }
});
$('#status_dropdown').change(function () {
    filterColumns();
});
$('#country_dropdown').change(function () {
    filterColumns();
});
$('#organisation_dropdown').change(function () {
    filterColumns();
});""")

                return output
            response.s3.postp = postp

            output = s3_rest_controller("supply", "item_entity")
            return output

        # =====================================================================
        # Pass variables back to global scope (response.s3.*)
        return dict (
                supply_item_id = supply_item_id,
                item_id = item_id,
                item_pack_id = item_pack_id,
                item_category_represent = item_category_represent,
                supply_item_represent = supply_item_represent,
                supply_brand_represent = supply_brand_represent,
                item_pack_represent = item_pack_represent,
                item_pack_virtualfields = item_pack_virtualfields,
                resource_duplicate = resource_duplicate,
                item_duplicate = item_duplicate,
                supply_item_add = supply_item_add,
                catalog_item_search = catalog_item_search,
                supply_item_controller = supply_item_controller,
                item_entity_controller = item_entity_controller,
            )

    # Provide a handle to this load function
    s3mgr.loader(supply_tables,
                 "supply_brand",
                 "supply_catalog",
                 "supply_item_category",
                 "supply_item",
                 "supply_item_entity",
                 "supply_catalog_item",
                 "supply_item_pack",
                 "supply_item_alt"
                 )

# END =========================================================================

