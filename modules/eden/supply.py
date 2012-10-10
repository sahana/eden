# -*- coding: utf-8 -*-

""" Sahana Eden Supply Model

    @copyright: 2009-2012 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ["S3SupplyModel",
           "supply_item_rheader",
           "SupplyItemPackVirtualFields",
           "supply_item_controller",
           "supply_item_entity_controller",
          ]

import re

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage

from ..s3 import *
from eden.layouts import S3AddResourceLink

# @ToDo: Put the most common patterns at the top to optimise
um_patterns = ["\sper\s?(.*)$",                         # CHOCOLATE, per 100g
               #"\((.*)\)$",                            # OUTWARD REGISTER for shipping (50 sheets)
               "([0-9]+\s?(gramm?e?s?|L|g|kg))$",       # Navarin de mouton 285 grammes
               ",\s(kit|pair|btl|bottle|tab|vial)\.?$", # STAMP, IFRC, Englishlue, btl.
               "\s(bottle)\.?$",                        # MINERAL WATER, 1.5L bottle
               ",\s((bag|box|kit) of .*)\.?$",          # (bag, diplomatic) LEAD SEAL, bag of 100
               ]

# =============================================================================
class S3SupplyModel(S3Model):
    """
        Generic Supply functionality such as catalogs and items that is used
        across multiple modules.

        @ToDo: Break this class up where possible
               - is this just supply_item_alt?
    """

    names = ["supply_brand",
             "supply_catalog",
             "supply_item_category",
             "supply_item",
             "supply_item_entity",
             "supply_catalog_item",
             "supply_item_pack",
             "supply_item_alt",
             "supply_item_id",
             "supply_item_entity_id",
             "supply_item_pack_id",
             "supply_kit_item",
             "supply_item_represent",
             "supply_item_category_represent",
             "supply_item_add",
             "supply_item_duplicate_fields",
             "supply_item_pack_virtualfields",
            ]

    def model(self):

        T = current.T
        db = current.db
        settings = current.deployment_settings

        # Shortcuts
        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # =====================================================================
        # Brand
        #
        tablename = "supply_brand"
        table = define_table(tablename,
                             Field("name", length=128, notnull=True, unique=True,
                                   label = T("Name")),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_BRAND = T("Add Brand")
        crud_strings[tablename] = Storage(
            title_create = ADD_BRAND,
            title_display = T("Brand Details"),
            title_list = T("Brands"),
            title_update = T("Edit Brand"),
            title_search = T("Search Brands"),
            subtitle_create = T("Add New Brand"),
            label_list_button = T("List Brands"),
            label_create_button = ADD_BRAND,
            label_delete_button = T("Delete Brand"),
            msg_record_created = T("Brand added"),
            msg_record_modified = T("Brand updated"),
            msg_record_deleted = T("Brand deleted"),
            msg_list_empty = T("No Brands currently registered"))

        # Reusable Field
        brand_id = S3ReusableField("brand_id", table, sortby="name",
                    requires = IS_NULL_OR(IS_ONE_OF(db, "supply_brand.id",
                                                    "%(name)s",
                                                    sort=True)),
                    represent = self.supply_brand_represent,
                    label = T("Brand"),
                    comment=S3AddResourceLink(c="supply",
                                              f="brand",
                                              label=ADD_BRAND,
                                              title=T("Brand"),
                                              tooltip=T("The list of Brands are maintained by the Administrators.")),
                    ondelete = "RESTRICT")

        # =====================================================================
        # Catalog (of Items)
        #
        tablename = "supply_catalog"
        table = define_table(tablename,
                             Field("name", length=128, notnull=True, unique=True,
                                   label = T("Name")),
                             self.org_organisation_id(),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_CATALOG = T("Add Catalog")
        crud_strings[tablename] = Storage(
            title_create = ADD_CATALOG,
            title_display = T("Catalog Details"),
            title_list = T("Catalogs"),
            title_update = T("Edit Catalog"),
            title_search = T("Search Catalogs"),
            subtitle_create = T("Add New Catalog"),
            label_list_button = T("List Catalogs"),
            label_create_button = ADD_CATALOG,
            label_delete_button = T("Delete Catalog"),
            msg_record_created = T("Catalog added"),
            msg_record_modified = T("Catalog updated"),
            msg_record_deleted = T("Catalog deleted"),
            msg_list_empty = T("No Catalogs currently registered"))

        # Reusable Field
        catalog_id = S3ReusableField("catalog_id", table,
                    sortby="name",
                    requires = IS_NULL_OR(
                                   IS_ONE_OF( # Restrict to catalogs the user can update
                                              db(current.auth.s3_accessible_query("update", table)),
                                              "supply_catalog.id",
                                              "%(name)s",
                                              sort=True,
                                              )
                                          ),
                    represent = lambda id: \
                        s3_get_db_field_value(tablename = "supply_catalog",
                                              fieldname = "name",
                                              look_up_value = id) or current.messages.NONE,
                    default = 1,
                    label = T("Catalog"),
                    comment=S3AddResourceLink(c="supply",
                                              f="catalog",
                                              label=ADD_CATALOG,
                                              title=T("Catalog"),
                                              tooltip=T("The list of Catalogs are maintained by the Administrators.")),
                    ondelete = "RESTRICT")

        # Categories as component of Catalogs
        add_component("supply_item_category", supply_catalog="catalog_id")

        # Catalog Items as component of Catalogs
        add_component("supply_catalog_item", supply_catalog="catalog_id")

        # =====================================================================
        # Item Category
        #
        asset = settings.has_module("asset")
        vehicle = settings.has_module("vehicle")

        tablename = "supply_item_category"
        table = define_table(tablename,
                             catalog_id(),
                             #Field("level", "integer"),
                             Field("parent_item_category_id",
                                   "reference supply_item_category",
                                   label = T("Parent"),
                                   ondelete = "RESTRICT"),
                             Field("code", length=16,
                                   label = T("Code"),
                                   #required = True
                                   ),
                             Field("name", length=128,
                                   label = T("Name")
                                   ),
                             Field("can_be_asset", "boolean",
                                   default=True,
                                   readable=asset,
                                   writable=asset,
                                   label=T("Items in Category can be Assets")),
                             Field("is_vehicle", "boolean",
                                   default=False,
                                   readable=vehicle,
                                   writable=vehicle,
                                   label=T("Items in Category are Vehicles")),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_ITEM_CATEGORY = T("Add Item Category")
        crud_strings[tablename] = Storage(
            title_create = ADD_ITEM_CATEGORY,
            title_display = T("Item Category Details"),
            title_list = T("Item Categories"),
            title_update = T("Edit Item Category"),
            title_search = T("Search Item Categories"),
            subtitle_create = T("Add New Item Category"),
            label_list_button = T("List Item Categories"),
            label_create_button = ADD_ITEM_CATEGORY,
            label_delete_button = T("Delete Item Category"),
            msg_record_created = T("Item Category added"),
            msg_record_modified = T("Item Category updated"),
            msg_record_deleted = T("Item Category deleted"),
            msg_list_empty = T("No Item Categories currently registered"))

        # Reusable Field
        item_category_requires = IS_NULL_OR(IS_ONE_OF(db,
                                                    "supply_item_category.id",
                                                    label = lambda v: \
                                                        self.item_category_represent(v, False),
                                                    sort=True))

        item_category_comment = S3AddResourceLink(c="supply",
                                                  f="item_category",
                                                  label=ADD_ITEM_CATEGORY,
                                                  title=T("Item Category"),
                                                  tooltip=ADD_ITEM_CATEGORY)

        table.parent_item_category_id.requires = item_category_requires
        table.parent_item_category_id.represent = self.item_category_represent

        item_category_id = S3ReusableField("item_category_id", table,
                                           sortby="name",
                                           requires=item_category_requires,
                                           represent=self.item_category_represent,
                                           label = T("Category"),
                                           comment = item_category_comment,
                                           ondelete = "RESTRICT")
        item_category_id_script = SCRIPT(
'''$(document).ready(function(){
 S3FilterFieldChange({
  'FilterField':'catalog_id',
  'Field':'item_category_id',
  'FieldPrefix':'supply',
  'FieldResource':'item_category',
 })
})''')


        # Categories as component of Categories
        add_component("supply_item_category",
                      supply_item_category="parent_item_category_id")

        def supply_item_category_onvalidate(form):
            """
                Checks that either a Code OR a Name are entered
            """
            # If their is a tracking number check that it is unique within the org
            if not (form.vars.code or form.vars.name):
                form.errors.code = form.errors.name = T("An Item Category must have a Code OR a Name.")

        self.configure(tablename,
                       onvalidation = supply_item_category_onvalidate,
                       )

        # =====================================================================
        # Item
        #
        #  These are Template items
        #  Instances of these become Inventory Items & Request items
        #
        tablename = "supply_item"
        table = define_table(tablename,
                             catalog_id(),
                             # Needed to auto-create a catalog_item
                             item_category_id(script = item_category_id_script),
                             Field("name", length=128, notnull=True,
                                   label = T("Name"),
                                   ),
                             Field("code", length=16,
                                   label = T("Code"),
                                   ),
                             Field("um", length=128, notnull=True,
                                   label = T("Unit of Measure"),
                                   default = "piece"
                                   ),
                             brand_id(),
                             Field("kit", "boolean",
                                   default=False,
                                   label=T("Kit?")),
                             Field("model", length=128,
                                   label = T("Model/Type"),
                                   ),
                             Field("year", "integer",
                                   label = T("Year of Manufacture")),
                             Field("weight", "double",
                                   label = T("Weight (kg)"),
                                   represent = lambda v, row=None: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2)
                                   ),
                             Field("length", "double",
                                   label = T("Length (m)"),
                                   represent = lambda v, row=None: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2)
                                   ),
                             Field("width", "double",
                                   label = T("Width (m)"),
                                   represent = lambda v, row=None: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2)
                                   ),
                             Field("height", "double",
                                   label = T("Height (m)"),
                                   represent = lambda v, row=None: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2)
                                   ),
                             Field("volume", "double",
                                   label = T("Volume (m3)"),
                                   represent = lambda v, row=None: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2)
                                   ),
                             # These comments do *not* pull through to an Inventory's Items or a Request's Items
                             s3_comments(),
                             *s3_meta_fields()
                            )

        # Categories in Progress
        #table.item_category_id_0.label = T("Category")
        #table.item_category_id_1.readable = table.item_category_id_1.writable = False
        #table.item_category_id_2.readable = table.item_category_id_2.writable = False

        # CRUD strings
        ADD_ITEM = T("Add New Item")
        crud_strings[tablename] = Storage(
            title_create = ADD_ITEM,
            title_display = T("Item Details"),
            title_list = T("Items"),
            title_update = T("Edit Item"),
            title_search = T("Search Items"),
            subtitle_create = T("Add New Item"),
            label_list_button = T("List Items"),
            label_create_button = ADD_ITEM,
            label_delete_button = T("Delete Item"),
            msg_record_created = T("Item added"),
            msg_record_modified = T("Item updated"),
            msg_record_deleted = T("Item deleted"),
            msg_list_empty = T("No Items currently registered"),
            msg_match = T("Matching Items"),
            msg_no_match = T("No Matching Items")
            )

        # Reusable Field
        supply_item_id = S3ReusableField("item_id", table, sortby="name", # 'item_id' for backwards-compatibility
                    requires = IS_ONE_OF(db, "supply_item.id",
                                         self.supply_item_represent,
                                         sort=True),
                    represent = self.supply_item_represent,
                    label = T("Item"),
                    widget = S3AutocompleteWidget("supply", "item"),
                    #widget = S3SearchAutocompleteWidget(
                    #                get_fieldname = "item_id",
                    #                tablename = "supply_catalog_item",
                    #                represent = lambda id: \
                    #                    self.supply_item_represent(id,
                    #                                               show_link=False,
                    #                                               # @ToDo: this doesn't work
                    #                                               show_um=False),
                    #                ),
                    comment=S3AddResourceLink(c="supply",
                                              f="item",
                                              label=ADD_ITEM,
                                              title=T("Item"),
                                              tooltip=T("Type the name of an existing catalog item OR Click 'Add New Item' to add an item which is not in the catalog.")),
                    ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Item Search Method
        #
        report_options = Storage(
            search=[S3SearchSimpleWidget(
                        name="item_search_text",
                        label=T("Search"),
                        comment=T("Search for an item by its code, name, model and/or comment."),
                        field=["code",
                               "name",
                               "model",
                               #"item_category_id$name",
                               "comments" ]
                      ),
                      S3SearchOptionsWidget(
                        name="item_search_brand",
                        label=T("Brand"),
                        comment=T("Search for an item by brand."),
                        field="brand_id",
                        represent ="%(name)s",
                        cols = 3
                      ),
                      S3SearchOptionsWidget(
                        name="item_search_year",
                        label=T("Year"),
                        comment=T("Search for an item by Year of Manufacture."),
                        field="year",
                        #represent ="%(name)s",
                        cols = 1
                      ),
                   ],

            defaults=Storage(
                             rows="name",
                             cols="item_category_id",
                             fact="brand_id",
                             aggregate="count",
                            ),
            hide_comments=True,
        )
        item_search = S3Search(advanced=report_options.get("search"))

        configure(tablename,
                  onaccept = self.supply_item_onaccept,
                  orderby = table.name,
                  search_method = item_search,
                  report_options = report_options,
                  )

        # Catalog Items as component of Items
        add_component("supply_catalog_item", supply_item="item_id")

        # Packs as component of Items
        add_component("supply_item_pack", supply_item="item_id")

        if settings.get_supply_use_alt_name():
            # Alternative Items as component of Items
            add_component("supply_item_alt", supply_item="item_id")

        # Inventory Items as component of Items
        add_component("inv_inv_item", supply_item="item_id")

        # Order Items as component of Items
        add_component("inv_recv_item", supply_item="item_id")

        # Procurement Plan Items as component of Items
        add_component("proc_plan_item", supply_item="item_id")

        # Request Items as component of Items
        add_component("req_req_item", supply_item="item_id")

        # Supply Kit Items as component of Items
        add_component("supply_kit_item", supply_item="parent_item_id")
        #add_component("supply_item", supply_item = dict(joinby="parent_item_id",
        #                                                alias="kit_item",
        #                                                link="supply_kit_item",
        #                                                actuate="hide",
        #                                                key="item_id"))

        # =====================================================================
        # Catalog Item
        #
        # This resource is used to link Items with Catalogs (n-to-n)
        # Item Categories will also be catalog specific
        #
        tablename = "supply_catalog_item"
        table = define_table(tablename,
                             catalog_id(),
                             item_category_id("item_category_id",
                                              #label = T("Group"),
                                              # Filters item_category_id based on catalog_id
                                              script = item_category_id_script,
                                            ),
                             supply_item_id(script = None), # No Item Pack Filter
                             s3_comments(), # These comments do *not* pull through to an Inventory's Items or a Request's Items
                             *s3_meta_fields())

        # CRUD strings
        ADD_ITEM = T("Add Catalog Item")
        crud_strings[tablename] = Storage(
            title_create = ADD_ITEM,
            title_display = T("Item Catalog Details"),
            title_list = T("Catalog Items"),
            title_update = T("Edit Catalog Item"),
            title_search = T("Search Catalog Items"),
            subtitle_create = T("Add Item to Catalog"),
            label_list_button = T("List Catalog Items"),
            label_create_button = ADD_ITEM,
            label_delete_button = T("Delete Catalog Item"),
            msg_record_created = T("Catalog Item added"),
            msg_record_modified = T("Catalog Item updated"),
            msg_record_deleted = T("Catalog Item deleted"),
            msg_list_empty = T("No Catalog Items currently registered"),
            msg_match = T("Matching Catalog Items"),
            msg_no_match = T("No Matching Catalog Items")
            )

        # ---------------------------------------------------------------------
        # Catalog Item Search Method
        #

        def catalog_item_search_simple_widget(type):
            return S3SearchSimpleWidget(
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

        catalog_item_search = S3Search(
            simple=(catalog_item_search_simple_widget("simple") ),
            advanced=(catalog_item_search_simple_widget("advanced"),
                      S3SearchOptionsWidget(
                         name="catalog_item_search_catalog",
                         label=T("Catalog"),
                         comment=T("Search for an item by catalog."),
                         field="catalog_id",
                         represent ="%(name)s",
                         cols = 3
                       ),
                       S3SearchOptionsWidget(
                         name="catalog_item_search_category",
                         label=T("Category"),
                         comment=T("Search for an item by category."),
                         field="item_category_id",
                         represent = lambda id: \
                            self.item_category_represent(id, use_code=False),
                         cols = 3
                       ),
                       S3SearchOptionsWidget(
                         name="catalog_item_search_brand",
                         label=T("Brand"),
                         comment=T("Search for an item by brand."),
                         field="item_id$brand_id",
                         represent ="%(name)s",
                         cols = 3
                       ),
            )
        )

        configure(tablename,
                  search_method = catalog_item_search,)

        # ---------------------------------------------------------------------
        # Calculate once, instead of for each record
        item_duplicate_fields = {}
        for tablename in ["supply_item", "supply_catalog_item"]:
            table = self[tablename]
            item_duplicate_fields[tablename] = [field.name for field in table
                                                if field.writable and
                                                field.name != "id"]

        configure("supply_item", deduplicate=self.item_duplicate)
        configure("supply_catalog_item", deduplicate=self.item_duplicate)
        configure("supply_item_category", deduplicate=self.item_duplicate)

        # =====================================================================
        # Item Pack
        #
        #  Items can be distributed in different containers
        #
        tablename = "supply_item_pack"
        table = define_table(tablename,
                             supply_item_id(empty=False),
                             Field("name", length=128,
                                   default = T("piece"),
                                   notnull=True, # Ideally this would reference another table for normalising Pack names
                                   label = T("Name"),
                                   ),
                             Field("quantity", "double",
                                   notnull=True,
                                   label = T("Quantity"),
                                   represent = lambda v, row=None: IS_FLOAT_AMOUNT.represent(v, precision=2)
                                   ),
                             s3_comments(),
                             *s3_meta_fields())



        # CRUD strings
        ADD_ITEM_PACK = T("Add Item Pack")
        crud_strings[tablename] = Storage(
            title_create = ADD_ITEM_PACK,
            title_display = T("Item Pack Details"),
            title_list = T("Item Packs"),
            title_update = T("Edit Item Pack"),
            title_search = T("Search Item Packs"),
            subtitle_create = T("Add New Item Pack"),
            label_list_button = T("List Item Packs"),
            label_create_button = ADD_ITEM_PACK,
            label_delete_button = T("Delete Item Pack"),
            msg_record_created = T("Item Pack added"),
            msg_record_modified = T("Item Pack updated"),
            msg_record_deleted = T("Item Pack deleted"),
            msg_list_empty = T("No Item Packs currently registered"))

        # ---------------------------------------------------------------------
        # Reusable Field
        item_pack_id = S3ReusableField("item_pack_id", table,
                    sortby="name",
                    # Do not display any packs initially
                    # will be populated by S3FilterFieldChange
                    requires = IS_ONE_OF_EMPTY_SELECT(db,
                                         "supply_item_pack.id",
                                         self.item_pack_represent,
                                         sort=True,
                                         # @ToDo: Enforce "Required" for imports
                                         # @ToDo: Populate based on item_id in controller instead of IS_ONE_OF_EMPTY_SELECT
                                         # filterby = "item_id",
                                         # filter_opts = [....],
                                         ),
                    represent = self.item_pack_represent,
                    label = T("Pack"),
                    #comment=S3AddResourceLink(c="supply",
                    #                          f="item_pack",
                    #                          label=ADD_ITEM_PACK,
                    #                          title=T("Item Packs"),
                    #                          tooltip=T("The way in which an item is normally distributed")),
                    script = SCRIPT('''
S3FilterFieldChange({
 'FilterField':'item_id',
 'Field':'item_pack_id',
 'FieldResource':'item_pack',
 'FieldPrefix':'supply',
 'msgNoRecords':S3.i18n.no_packs,
 'fncPrep':fncPrepItem,
 'fncRepresent':fncRepresentItem
})'''),
                    ondelete = "RESTRICT")

        #def record_pack_quantity(r):
        #    item_pack_id = r.get("item_pack_id", None)
        #    if item_pack_id:
        #        return s3_get_db_field_value(tablename = "supply_item_pack",
        #                                     fieldname = "quantity",
        #                                     look_up_value = item_pack_id)
        #    else:
        #        return None

        configure(tablename,
                  deduplicate=self.item_pack_duplicate)

        # Inventory items as component of Packs
        add_component("inv_inv_item", supply_item_pack="item_pack_id")

        # =====================================================================
        # Supply Kit Item Table
        #
        # For defining what items are in a kit

        tablename = "supply_kit_item"
        table = define_table(tablename,
                             supply_item_id("parent_item_id",
                                            label = T("Parent Item"),
                                            comment = None),
                             supply_item_id("item_id",
                                            label = T("Kit Item")),
                             Field("quantity", "double",
                                   label = T("Quantity"),
                                   represent = lambda v, row=None: \
                                    IS_FLOAT_AMOUNT.represent(v, precision=2)
                                   ),
                             item_pack_id(),
                             s3_comments(),
                             *s3_meta_fields())

        # =====================================================================
        # Alternative Items
        #
        #  If the desired item isn't found, then these are designated as
        #  suitable alternatives
        #
        tablename = "supply_item_alt"
        table = define_table(tablename,
                             supply_item_id(notnull=True),
                             Field("quantity",
                                   "double",
                                   label = T("Quantity"),
                                   comment = DIV(_class = "tooltip",
                                                 _title = "%s|%s" %
                                                       (T("Quantity"),
                                                        T("The number of Units of Measure of the Alternative Items which is equal to One Unit of Measure of the Item")
                                                       )
                                               ),
                                   default = 1,
                                   notnull=True,
                                   represent = lambda v, row=None: IS_FLOAT_AMOUNT.represent(v, precision=2)),
                             supply_item_id("alt_item_id",
                                            notnull=True),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        ADD_ALT_ITEM = T("Add Alternative Item")
        crud_strings[tablename] = Storage(
            title_create = ADD_ALT_ITEM,
            title_display = T("Alternative Item Details"),
            title_list = T("Alternative Items"),
            title_update = T("Edit Alternative Item"),
            title_search = T("Search Alternative Items"),
            subtitle_create = T("Add New Alternative Item"),
            label_list_button = T("List Alternative Items"),
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
        #item_alt_id = S3ReusableField("item_alt_id", table,
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
        # Item Super-Entity
        #
        # This super entity provides a common way to provide a foreign key to supply_item
        # - it allows searching/reporting across Item types easily.
        #
        item_types = Storage(
                            inv_inv_item = T("Warehouse Stock"),
                            inv_recv_item = T("Order Item"),
                            proc_plan_item = T("Planned Procurement Item"),
                            )

        tablename = "supply_item_entity"
        table = self.super_entity(tablename, "item_entity_id", item_types,
                                  # @ToDo: Make Items Trackable?
                                  #super_link("track_id", "sit_trackable"),
                                  #location_id(),
                                  supply_item_id(represent = lambda id: \
                                            self.supply_item_represent(id,
                                                                       show_um=False,
                                                                       show_link=True)),
                                  item_pack_id(),
                                  Field("quantity", "double",
                                        label = T("Quantity"),
                                        default = 1.0,
                                        notnull = True),
                                  *s3_ownerstamp()
                                  )

        # ---------------------------------------------------------------------
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
        item_entity_search = S3Search(
            # Advanced Search only
            advanced=(S3SearchSimpleWidget(
                        name="item_entity_search_text",
                        label=T("Search"),
                        comment=T("Search for an item by text."),
                        field=[ "item_id$name",
                                #"item_id$item_category_id$name",
                                #"site_id$name"
                                ]
                      ),
                      S3SearchOptionsWidget(
                        name="item_entity_search_category",
                        label=T("Code Share"),
                        field="item_id$item_category_id",
                        represent ="%(name)s",
                        comment=T("If none are selected, then all are searched."),
                        cols = 2
                      ),
                      #S3SearchOptionsWidget(
                      #  name="item_entity_search_country",
                      #  label=current.messages.COUNTRY,
                      #  field="country",
                      #  represent ="%(name)s",
                      #  comment=T("If none are selected, then all are searched."),
                      #  cols = 2
                      #),
            ))

        # ---------------------------------------------------------------------
        configure(tablename,
                  search_method = item_entity_search)

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                supply_item_id = supply_item_id,
                supply_item_entity_id = item_id,
                supply_item_pack_id = item_pack_id,
                supply_item_represent = self.supply_item_represent,
                supply_item_category_represent = self.item_category_represent,
                supply_item_pack_virtualfields = SupplyItemPackVirtualFields,
                supply_item_duplicate_fields = item_duplicate_fields,
                supply_item_add = self.supply_item_add,
                supply_item_pack_represent = self.item_pack_represent,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """ Return safe defaults for names in case the model is disabled """

        supply_item_id = S3ReusableField("item_id", "integer",
                                         writable=False,
                                         readable=False)
        item_id = S3ReusableField("item_entity_id", "integer",
                                  writable=False,
                                  readable=False)()
        item_pack_id = S3ReusableField("item_pack_id", "integer",
                                       writable=False,
                                       readable=False)

        return Storage(
                supply_item_id = supply_item_id,
                supply_item_entity_id = item_id,
                supply_item_pack_id = item_pack_id,
                supply_item_pack_virtualfields = None,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def supply_item_add (quantity_1, pack_quantity_1,
                         quantity_2, pack_quantity_2):
        """
            Adds item quantities together, accounting for different pack
            quantities.
            Returned quantity according to pack_quantity_1

            Used by controllers/inv.py
        """

        if pack_quantity_1 == pack_quantity_2:
            # Faster calculation
            quantity = quantity_1 + quantity_2
        else:
            quantity = ((quantity_1 * pack_quantity_1) +
                        (quantity_2 * pack_quantity_2)) / pack_quantity_1
        return quantity

    # -------------------------------------------------------------------------
    @staticmethod
    def supply_brand_represent(id):
        """
        """

        if not id:
            return current.messages.NONE

        db = current.db
        table = db.supply_brand
        record = db(table.id == id).select(table.name,
                                           limitby=(0, 1)).first()
        if record:
            return record.name
        else:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def item_category_represent(id, use_code=True):
        """
        """

        if not id:
            return current.messages.NONE

        db = current.db
        cache = current.s3db.cache
        table = db.supply_item_category

        represent = ""
        item_category_id = id
        while item_category_id:
            query = (table.id == item_category_id)
            r = db(query).select(table.catalog_id,
                                 table.code,
                                 table.name,
                                 table.parent_item_category_id,
                                 # left = table.on(table.id == table.parent_item_category_id), Doesn't work
                                 limitby=(0, 1),
                                 cache=cache).first()

            if (r.code and use_code) or (not r.name and r.code):
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

            # Feed the loop
            item_category_id = r.parent_item_category_id

        catalog = s3_get_db_field_value(tablename = "supply_catalog",
                                        fieldname = "name",
                                        look_up_value = r.catalog_id)

        if catalog:
            return "%s > %s" % (catalog, represent)
        else:
            return represent

    # -------------------------------------------------------------------------
    @staticmethod
    def item_represent(id):
        """
            Represent an item entity in option fields or list views
            - unused, we use VirtualField instead
        """

        if not id:
            return current.messages.NONE

        db = current.db

        if isinstance(id, Row) and "instance_type" in id:
            # Do not repeat the lookup if already done by IS_ONE_OF
            item = id
            instance_type = item.instance_type
        else:
            item_table = db.supply_item_entity
            item = db(item_table._id == id).select(item_table.instance_type,
                                                   limitby=(0, 1)).first()
            try:
                instance_type = item.instance_type
            except:
                return current.messages.UNKNOWN_OPT

        T = current.T
        if instance_type == "inv_inv_item":
            item_str = T("In Stock")
        elif instance_type == "inv_recv_item":
            s3db = current.s3db
            itable = s3db[instance_type]
            rtable = s3db.inv_recv
            query = (itable.item_entity_id == id) & \
                    (rtable.id == itable.recv_id)
            eta = db(query).select(rtable.eta,
                                   limitby=(0, 1)).first().eta
            item_str = T("Due %(date)s") % dict(date=eta)
        else:
            return current.messages.UNKNOWN_OPT

        return item_str

    # -------------------------------------------------------------------------
    @staticmethod
    def supply_item_represent(id,
                              # Needed for S3SearchAutocompleteWidget
                              show_um = False,
                              show_link = True):
        """
            Representation of a supply_item
        """

        if not id:
            return current.messages.NONE

        db = current.db
        table = db.supply_item
        btable = db.supply_brand
        query = (table.id == id)
        r = db(query).select(table.name,
                             table.model,
                             table.um,
                             btable.name,
                             left = btable.on(table.brand_id == btable.id),
                             limitby=(0, 1)).first()
        try:
            represent = [r.supply_item.name,
                         r.supply_brand.name,
                         r.supply_item.model]
        except:
            return current.messages.UNKNOWN_OPT
        represent = [rep for rep in represent if rep]
        represent = " - ".join(represent)

        if show_um and r.supply_item.um:
            represent = "%s (%s)" % (represent, r.supply_item.um)

        local_request = current.request
        local_request.extension = "html"
        if show_link:
            return A(represent,
                     _href = URL(r = local_request,
                                 c = "supply",
                                 f = "item",
                                 args = [id]
                                 )
                     )
        else:
            return represent

    # ---------------------------------------------------------------------
    @staticmethod
    def item_pack_represent(id):
        """
        """

        if not id:
            return current.messages.NONE

        db = current.db
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
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def item_duplicate(job):
        """
            Callback function used to look for duplicates during
            the import process
        """

        tablename = job.tablename

        if tablename == "supply_item":
            job.data.update(item_um_from_name(job.data.name,
                                              job.data.um)
                            )

        if tablename in ["supply_item", "supply_catalog_item"]:
            resource_duplicate(tablename, job,
                               current.s3db.supply_item_duplicate_fields[tablename])

        elif tablename == "supply_item_category":
            resource_duplicate("supply_item_category", job,
                               fields = ["catalog_id",
                                         "parent_item_category_id",
                                         "code",
                                         "name"])

    # -------------------------------------------------------------------------
    @staticmethod
    def item_pack_duplicate(job):
        """
            Callback function used to look for duplicates during
            the import process
        """

        # An Item Pack is a duplicate if both the Name & Item are identical
        resource_duplicate(job.tablename, job,
                           fields = ["name",
                                     "item_id",
                                     "quantity",
                                    ])

    # -------------------------------------------------------------------------
    @staticmethod
    def supply_item_onaccept(form):
        """
            Create a catalog_item for this item
            Update the UM (Unit of Measure) in the supply_item_pack table
        """

        db = current.db
        auth = current.auth

        vars = form.vars
        item_id = vars.id
        catalog_id = vars.catalog_id
        catalog_item_id = None


        citable = db.supply_catalog_item
        query = (citable.item_id == item_id) & \
                (citable.deleted == False )
        rows = db(citable).select(citable.id)
        if not len(rows):
        # Create supply_catalog_item
            catalog_item_id = \
                citable.insert(catalog_id = catalog_id,
                               item_category_id = vars.item_category_id,
                               item_id = item_id
                               )
        # Update if the catalog/category has changed - if there is only supply_catalog_item
        elif len(rows) == 1:
            catalog_item_id = rows.first().id
            catalog_item_id = \
                db(citable.id == catalog_item_id
                   ).update(catalog_id = catalog_id,
                            item_category_id = vars.item_category_id,
                            item_id = item_id
                            )
        #auth.s3_set_record_owner(citable, catalog_item_id, force_update=True)

        # Update UM
        um = vars.um or db.supply_item.um.default
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

        if vars.kit:
            # Go to that tab afterwards
            url = URL(args=["[id]", "kit_item"])
            current.s3db.configure("supply_item",
                                   create_next=url,
                                   update_next=url,
                                  )

# =============================================================================
def item_um_from_name(name, um):
    """
        Retrieve the Unit of Measure from a name
    """
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

# =============================================================================
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

    if job.tablename == tablename:
        table = job.table
        data = job.data
        query = None
        db = current.db
        if not fields:
            fields = [field.name for field in db[tablename]
                      if field.writable and field.name != "id"]
        for field in fields:
            value = field in data and data[field] or None
            # Hack to get prepop working for Sahana Camp LA
            if value:
                try:
                    field_query = (table[field].lower() == value.lower())
                except:
                    field_query = (table[field] == value)

                # Hack for identifying Item duplicates basd on code
                if tablename == "supply_item" and field == "code":
                    _duplicate = db(field_query).select(table.id,
                                          limitby=(0, 1)).first()
                    if _duplicate:
                        job.id = _duplicate.id
                        job.method = job.METHOD.UPDATE
                        return

            # if not value:
                # # Workaround
                # if tablename == "supply_item_category" and field == "name":
                    # continue
                # field_query = (table[field] == None)
            # else:
                # try:
                    # field_query = (table[field].lower() == value.lower())
                # except:
                    # field_query = (table[field] == value)
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

# =============================================================================
def supply_item_rheader(r):
    """ Resource Header for Items """

    if r.representation == "html":
        item = r.record
        if item:

            T = current.T

            tabs = [
                    (T("Edit Details"), None),
                    (T("Packs"), "item_pack"),
                    (T("Alternative Items"), "item_alt"),
                    (T("In Inventories"), "inv_item"),
                    (T("Requested"), "req_item"),
                    (T("In Catalogs"), "catalog_item"),
                   ]
            if item.kit == True:
                tabs.append((T("Kit Items"), "kit_item"))
            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table

            rheader = DIV(TABLE(TR( TH("%s: " % table.name.label),
                                    item.name,
                                  ),
                                TR( TH("%s: " % table.brand_id.label),
                                    table.brand_id.represent(item.brand_id),
                                  ),
                                TR( TH("%s: " % table.model.label),
                                    item.model or current.messages.NONE,
                                  ),
                               ),
                          rheader_tabs
                         )
            return rheader
    return None

# =============================================================================
class SupplyItemPackVirtualFields(dict, object):
    """ Virtual Field for pack_quantity """

    def __init__(self, tablename):
        self.tablename = tablename

    def pack_quantity(self):
        try:
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
        except AttributeError:
            item_pack = None
        if item_pack:
            return item_pack.quantity
        else:
            return None

# =============================================================================
# Virtual Fields for category, country, organisation & status
class item_entity_virtualfields:
    # Fields to be loaded by sqltable as qfields
    # without them being list_fields
    # (These cannot contain VirtualFields)
    # In this case we just load it once to save a query in each method
    extra_fields = [
                "instance_type"
            ]

    # -------------------------------------------------------------------------
    def category(self):
        table = current.s3db.supply_item
        try:
            query = (table.id == self.supply_item_entity.item_id)
        except:
            # We are being instantiated inside one of the other methods
            return None
        record = current.db(query).select(table.item_category_id,
                                          limitby=(0, 1)).first()
        if record:
            return table.item_category_id.represent(record.item_category_id)
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    def country(self):
        country = None
        s3db = current.s3db
        etable = s3db.supply_item_entity
        instance_type = self.supply_item_entity.instance_type
        if instance_type == "inv_inv_item":
            tablename = instance_type
            itable = s3db[instance_type]
            otable = s3db.org_office
            try:
                query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                        (otable.site_id == itable.site_id)
            except:
                 # We are being instantiated inside one of the other methods
                return None
            record = current.db(query).select(otable.L0,
                                              limitby=(0, 1)).first()
            if record:
                country = record.L0 or current.T("Unknown")
        elif instance_type == "inv_recv_item":
            tablename = instance_type
            itable = s3db[instance_type]
            rtable = s3db.inv_recv
            otable = s3db.org_office
            try:
                query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                        (rtable.id == itable.recv_id) & \
                        (otable.site_id == rtable.site_id)
            except:
                 # We are being instantiated inside one of the other methods
                return None
            record = current.db(query).select(otable.L0,
                                              limitby=(0, 1)).first()
            if record:
                country = record.L0 or current.T("Unknown")
        elif instance_type == "proc_plan_item":
            tablename = instance_type
            itable = s3db[instance_type]
            ptable = s3db.proc_plan
            otable = s3db.org_office
            try:
                query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                        (ptable.id == itable.plan_id) & \
                        (otable.site_id == ptable.site_id)
            except:
                 # We are being instantiated inside one of the other methods
                return None
            record = current.db(query).select(otable.L0,
                                              limitby=(0, 1)).first()
            if record:
                country = record.L0 or current.T("Unknown")
        else:
            # @ToDo: Assets and req_items
            return current.messages.NONE
        return country or current.messages.NONE

    # -------------------------------------------------------------------------
    def organisation(self):
        organisation = None
        s3db = current.s3db
        etable = s3db.supply_item_entity
        instance_type = self.supply_item_entity.instance_type
        if instance_type == "inv_inv_item":
            tablename = instance_type
            itable = s3db[instance_type]
            otable = s3db.org_office
            try:
                query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                        (otable.site_id == itable.site_id)
            except:
                 # We are being instantiated inside one of the other methods
                return None
            record = current.db(query).select(otable.organisation_id,
                                              limitby=(0, 1)).first()
            if record:
                organisation = s3db.org_organisation_represent(record.organisation_id,
                                                               acronym=False)
        elif instance_type == "proc_plan_item":
            tablename = instance_type
            itable = s3db[instance_type]
            rtable = s3db.proc_plan
            otable = s3db.org_office
            try:
                query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                        (rtable.id == itable.plan_id) & \
                        (otable.site_id == rtable.site_id)
            except:
                 # We are being instantiated inside one of the other methods
                return None
            record = current.db(query).select(otable.organisation_id,
                                              limitby=(0, 1)).first()
            if record:
                organisation = organisation_represent(record.organisation_id,
                                                      acronym=False)
        elif instance_type == "inv_recv_item":
            tablename = instance_type
            itable = s3db[instance_type]
            rtable = s3db.inv_recv
            otable = s3db.org_office
            try:
                query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                        (rtable.id == itable.recv_id) & \
                        (otable.site_id == rtable.site_id)
            except:
                 # We are being instantiated inside one of the other methods
                return None
            record = current.db(query).select(otable.organisation_id,
                                              limitby=(0, 1)).first()
            if record:
                organisation = organisation_represent(record.organisation_id,
                                                      acronym=False)
        else:
            # @ToDo: Assets and req_items
            return current.messages.NONE
        return organisation or current.messages.NONE

    # -------------------------------------------------------------------------
    #def site(self):
    def contacts(self):
        #site = current.messages.NONE
        s3db = current.s3db
        etable = s3db.supply_item_entity
        instance_type = self.supply_item_entity.instance_type
        if instance_type == "inv_inv_item":
            tablename = instance_type
            itable = s3db[instance_type]
            try:
                query = (itable.item_entity_id == self.supply_item_entity[etable._id.name])
            except:
                 # We are being instantiated inside one of the other methods
                return None
            record = current.db(query).select(itable.site_id,
                                              limitby=(0, 1)).first()
        elif instance_type == "inv_recv_item":
            tablename = instance_type
            itable = s3db[instance_type]
            rtable = s3db.inv_recv
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
            itable = s3db[instance_type]
            ptable = s3db.proc_plan
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
            return current.messages.NONE

        #site = s3db.org_site_represent(record.site_id)
        #return site
        otable = s3db.org_office
        query = (otable.site_id == record.site_id)
        record = current.db(query).select(otable.id,
                                          otable.comments,
                                          limitby=(0, 1)).first()
        extension = current.request.extension
        if extension == "xls" or \
           extension == "pdf":
            if record.comments:
                return record.comments
            else:
                return current.messages.NONE
        elif record.comments:
            comments = s3_comments_represent(record.comments,
                                             show_link=False)
        else:
            comments = current.messages.NONE
        return A(comments,
                 _href = URL(f="office",
                             args = [record.id]))

    # -------------------------------------------------------------------------
    def status(self):
        status = None
        s3db = current.s3db
        etable = s3db.supply_item_entity
        instance_type = self.supply_item_entity.instance_type
        if instance_type == "inv_inv_item":
            tablename = instance_type
            itable = s3db[instance_type]
            try:
                query = (itable.item_entity_id == self.supply_item_entity[etable._id.name])
            except:
                # We are being instantiated inside one of the other methods
                return None
            record = current.db(query).select(itable.expiry_date,
                                              limitby=(0, 1)).first()
            if record:
                T = current.T
                if record.expiry_date:
                    status = T("Stock Expires %(date)s") % dict(date=record.expiry_date)
                else:
                   status = T("In Stock")
        elif instance_type == "proc_plan_item":
            tablename = instance_type
            itable = s3db[instance_type]
            rtable = s3db.proc_plan
            try:
                query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                        (rtable.id == itable.plan_id)
            except:
                # We are being instantiated inside one of the other methods
                return None
            record = current.db(query).select(rtable.eta,
                                              limitby=(0, 1)).first()
            if record:
                T = current.T
                if record.eta:
                    status = T("Planned %(date)s") % dict(date=record.eta)
                else:
                   status = T("Planned Procurement")
        elif instance_type == "inv_track_item":
            tablename = instance_type
            itable = s3db[instance_type]
            rtable = s3db.inv_recv
            try:
                query = (itable.item_entity_id == self.supply_item_entity[etable._id.name]) & \
                        (rtable.id == itable.send_inv_item_id)
            except:
                # We are being instantiated inside one of the other methods
                return None
            record = current.db(query).select(rtable.eta,
                                              limitby=(0, 1)).first()
            if record:
                T = current.T
                if record.eta:
                    status = T("Order Due %(date)s") % dict(date=record.eta)
                else:
                    status = T("On Order")
        else:
            # @ToDo: Assets and req_items
            return current.messages.NONE
        return status or current.messages.NONE

# =============================================================================
def supply_item_controller():
    """ RESTful CRUD controller """

    s3db = current.s3db

    # Inventory Items need proper accountability so are edited through inv_adj
    s3db.configure("inv_inv_item",
                   listadd=False,
                   deletable=False)

    def prep(r):
        if r.component and r.component.name == "inv_item":
            # Filter to just item packs for this Item
            inv_item_pack_requires = IS_ONE_OF(current.db,
                                               "supply_item_pack.id",
                                               s3db.supply_item_pack_represent,
                                               sort=True,
                                               filterby = "item_id",
                                               filter_opts = [r.record.id],
                                               )
            s3db.inv_inv_item.item_pack_id.requires = inv_item_pack_requires
        # Needs better workflow as no way to add the Kit Items
        # else:
            # caller = current.request.get_vars.get("caller", None)
            # if caller == "inv_kit_item_id":
                # field = r.table.kit
                # field.default = True
                # field.readable = field.writable = False

        return True
    current.response.s3.prep = prep

    return current.rest_controller("supply", "item",
                                   rheader=s3db.supply_item_rheader)

# =============================================================================
def supply_item_entity_controller():
    """
        RESTful CRUD controller
        - consolidated report of inv_item, recv_item & proc_plan_item
        @ToDo: Migrate JS to Static as part of migrating this to an
               S3Search Widget
    """

    T = current.T
    db = current.db
    s3db = current.s3db
    s3 = current.response.s3
    settings = current.deployment_settings

    tablename = "supply_item_entity"
    table = s3db[tablename]

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        title_create = T("Add Item"),
        title_display = T("Item Details"),
        title_list = T("Items"),
        title_update = T("Edit Item"),
        title_search = T("Search Items"),
        label_list_button = T("List Items"),
        label_create_button = T("Add Item"),
        label_delete_button = T("Delete Item"),
        msg_record_created = T("Item added"),
        msg_record_modified = T("Item updated"),
        msg_record_deleted = T("Item deleted"),
        msg_list_empty = T("No Items currently registered"),
        name_nice = T("Item"),
        name_nice_plural = T("Items"))

    table.virtualfields.append(item_entity_virtualfields())

    # Allow VirtualFields to be sortable/searchable
    s3.no_sspag = True

    s3db.configure(tablename,
                   deletable = False,
                   insertable = False,
                   # @ToDo: Allow VirtualFields to be used to Group Reports
                   #report_groupby = "category",
                   list_fields = [(T("Category"), "category"),
                                  "item_id",
                                  "quantity",
                                  (T("Unit of Measure"), "item_pack_id"),
                                  (T("Status"), "status"),
                                  (current.messages.COUNTRY, "country"),
                                  (T("Organization"), "organisation"),
                                  #(T("Office"), "site"),
                                  (T("Contacts"), "contacts"),
                                ])

    def postp(r, output):
        if r.interactive and not r.record:
            # Provide some manual Filters above the list
            rheader = DIV()

            # Filter by Category
            table = s3db.supply_item_category
            etable = s3db.supply_item_entity
            itable = s3db.supply_item
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
            if settings.has_module("inv"):
                select.append(OPTION(T("In Stock")))
                select.append(OPTION(T("On Order")))
            if settings.has_module("proc"):
                select.append(OPTION(T("Planned Procurement")))
            rheader.append(DIV(B("%s:" % T("Filter by Status")),
                               BR(),
                               select,
                               _class="rfilter"))

            output["rheader"] = rheader

            # Find Offices with Items
            # @ToDo: Other Site types (how to do this as a big Join?)
            table = s3db.org_office
            otable = s3db.org_organisation
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
            if settings.has_module("inv"):
                iquery = query & (db.inv_inv_item.site_id == table.site_id)
                isites = db(iquery).select(distinct=True,
                                           *fields)
                rquery = query & (s3db.inv_track_item.send_inv_item_id == db.inv_recv.id) & \
                                 (db.inv_recv.site_id == table.site_id)
                rsites = db(rquery).select(distinct=True,
                                           *fields)
            if settings.has_module("proc"):
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
            s3.jquery_ready.append('''
function filterColumns(){
 var oTable=$('#list').dataTable()
 var values=''
 $('#category_dropdown option:selected').each(function(){
  values+=$(this).text()+'|'
 })
 var regex=(values==''?'':'^'+values.slice(0, -1)+'$')
 oTable.fnFilter('',1,false)
 oTable.fnFilter(regex,1,true,false)
 values=''
 $('#status_dropdown option:selected').each(function(){
  if($(this).text()=="''' + T("On Order") + '''"){
   values+=$(this).text()+'|'+"''' + T("Order") + '''.*"+'|'
  }else if($(this).text()=="''' + T("Planned Procurement") + '''"){
   values+="''' + T("Planned") + '''.*"+'|'
  }else{
   values+=$(this).text()+'|'+"''' + T("Stock") + '''.*"+'|'
  }
 })
 var regex=(values==''?'':'^'+values.slice(0,-1)+'$')
 oTable.fnFilter('',5,false)
 oTable.fnFilter(regex,5,true,false)
 values=''
 $('#country_dropdown option:selected').each(function(){
  values+=$(this).text()+'|'
 })
 var regex=(values==''?'':'^'+values.slice(0,-1)+'$')
 oTable.fnFilter('',6,false)
 oTable.fnFilter(regex,6,true,false)
 values=''
 $('#organisation_dropdown option:selected').each(function(){
  values+=$(this).text()+'|'
 })
 var regex=(values==''? '':'^'+values.slice(0,-1)+'$')
 oTable.fnFilter('',7,false)
 oTable.fnFilter(regex,7,true,false)
}
$('#category_dropdown').change(function(){
 filterColumns()
 var values=[]
 $('#category_dropdown option:selected').each(function(){
  values.push($(this).attr('name'))
 })
 if(values.length){
  $('#list_formats a').attr('href',function(){
   var href=this.href.split('?')[0]+'?item_entity.item_id$item_category_id='+values[0]
   for(i=1;i<=(values.length-1);i++){
    href=href+','+values[i]
   }
   return href
   })
 }else{
  $('#list_formats a').attr('href',function(){
   return this.href.split('?')[0]
  })
 }
})
$('#status_dropdown').change(function(){
 filterColumns()
})
$('#country_dropdown').change(function(){
 filterColumns()
})
$('#organisation_dropdown').change(function(){
 filterColumns()
})''')

        return output
    s3.postp = postp

    output = current.rest_controller("supply", "item_entity")
    return output

# END =========================================================================
