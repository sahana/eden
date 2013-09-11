# -*- coding: utf-8 -*-

""" Sahana Eden Supply Model

    @copyright: 2009-2013 (c) Sahana Software Foundation
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
           "S3SupplyDistributionModel",
           "supply_item_rheader",
           "supply_item_controller",
           "supply_item_entity_controller",
           "supply_catalog_rheader",
           "supply_item_entity_category",
           "supply_item_entity_country",
           "supply_item_entity_organisation",
           "supply_item_entity_contacts",
           "supply_item_entity_status",
           "supply_ItemRepresent",
           #"supply_ItemCategoryRepresent",
           ]

import re

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3AddResourceLink

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
             "supply_item_category_id",
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
             "supply_item_pack_quantity",
             ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        settings = current.deployment_settings

        # Shortcuts
        add_component = self.add_component
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        float_represent = IS_FLOAT_AMOUNT.represent

        NONE = current.messages["NONE"]

        if current.auth.permission.format == "html":
            i18n = {"in_inv": T("in Stock"),
                    "no_packs": T("No Packs for Item"),
                    }
            s3.js_global.append('''i18n.in_inv="%s"''' % i18n["in_inv"])
            s3.js_global.append('''i18n.no_packs="%s"''' % i18n["no_packs"])
            
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
        represent = S3Represent(lookup=tablename)
        brand_id = S3ReusableField("brand_id", table, sortby="name",
                    requires = IS_NULL_OR(IS_ONE_OF(db, "supply_brand.id",
                                                    represent,
                                                    sort=True)),
                    represent = represent,
                    label = T("Brand"),
                    comment=S3AddResourceLink(c="supply",
                                              f="brand",
                                              label=ADD_BRAND,
                                              title=T("Brand"),
                                              tooltip=T("The list of Brands are maintained by the Administrators.")),
                    ondelete = "RESTRICT"
                    )

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
        represent = S3Represent(lookup=tablename)
        catalog_id = S3ReusableField("catalog_id", table,
                    sortby="name",
                    requires = IS_NULL_OR(
                                   IS_ONE_OF( # Restrict to catalogs the user can update
                                              db(current.auth.s3_accessible_query("update", table)),
                                              "supply_catalog.id",
                                              represent,
                                              sort=True,
                                              )
                                          ),
                    represent = represent,
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

        item_category_represent = supply_ItemCategoryRepresent()
        item_category_represent_nocodes = supply_ItemCategoryRepresent(use_code=False)

        tablename = "supply_item_category"
        table = define_table(tablename,
                             catalog_id(),
                             #Field("level", "integer"),
                             Field("parent_item_category_id",
                                   "reference supply_item_category",
                                   label = T("Parent"),
                                   represent = item_category_represent,
                                   ondelete = "RESTRICT",
                                   ),
                             Field("code", length=16,
                                   label = T("Code"),
                                   #required = True,
                                   ),
                             Field("name", length=128,
                                   label = T("Name")),
                             Field("can_be_asset", "boolean",
                                   default=True,
                                   readable=asset,
                                   writable=asset,
                                   represent = s3_yes_no_represent,
                                   label=T("Items in Category can be Assets")),
                             Field("is_vehicle", "boolean",
                                   default=False,
                                   readable=vehicle,
                                   writable=vehicle,
                                   represent = s3_yes_no_represent,
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
        item_category_requires = IS_NULL_OR(
                                    IS_ONE_OF(db, "supply_item_category.id",
                                              item_category_represent_nocodes,
                                              sort=True)
                                    )

        item_category_comment = S3AddResourceLink(c="supply",
                                                  f="item_category",
                                                  label=ADD_ITEM_CATEGORY,
                                                  title=T("Item Category"),
                                                  tooltip=ADD_ITEM_CATEGORY
                                                  )

        table.parent_item_category_id.requires = item_category_requires

        item_category_id = S3ReusableField("item_category_id", table,
                                           sortby="name",
                                           requires=item_category_requires,
                                           represent=item_category_represent,
                                           label = T("Category"),
                                           comment = item_category_comment,
                                           ondelete = "RESTRICT"
                                           )
        item_category_script = '''
S3OptionsFilter({
 'triggerName':'catalog_id',
 'targetName':'item_category_id',
 'lookupPrefix':'supply',
 'lookupResource':'item_category',
})'''

        # Categories as component of Categories
        add_component("supply_item_category",
                      supply_item_category="parent_item_category_id")

        def supply_item_category_onvalidate(form):
            """
                Checks that either a Code OR a Name are entered
            """
            # If there is a tracking number check that it is unique within the org
            if not (form.vars.code or form.vars.name):
                error = form.errors
                errors.code = errors.name = T("An Item Category must have a Code OR a Name.")

        configure(tablename,
                  onvalidation = supply_item_category_onvalidate,
                  deduplicate = self.supply_item_category_duplicate,
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
                             item_category_id(
                                script = item_category_script
                                ),
                             Field("name", length=128, notnull=True,
                                   label = T("Name"),
                                   ),
                             Field("code", length=16,
                                   represent = lambda v: v or NONE,
                                   label = T("Code"),
                                   ),
                             Field("um", length=128, notnull=True,
                                   label = T("Unit of Measure"),
                                   default = "piece"
                                   ),
                             brand_id(),
                             Field("kit", "boolean",
                                   default=False,
                                   represent=lambda bool: \
                                    (bool and [T("Yes")] or
                                    [NONE])[0],
                                   label=T("Kit?")
                                   ),
                             Field("model", length=128,
                                   represent = lambda v: v or NONE,
                                   label = T("Model/Type"),
                                   ),
                             Field("year", "integer",
                                   represent = lambda v: v or NONE,
                                   label = T("Year of Manufacture")
                                   ),
                             Field("weight", "double",
                                   label = T("Weight (kg)"),
                                   represent = lambda v: \
                                    float_represent(v, precision=2)
                                   ),
                             Field("length", "double",
                                   label = T("Length (m)"),
                                   represent = lambda v: \
                                    float_represent(v, precision=2)
                                   ),
                             Field("width", "double",
                                   label = T("Width (m)"),
                                   represent = lambda v: \
                                    float_represent(v, precision=2)
                                   ),
                             Field("height", "double",
                                   label = T("Height (m)"),
                                   represent = lambda v: \
                                    float_represent(v, precision=2)
                                   ),
                             Field("volume", "double",
                                   label = T("Volume (m3)"),
                                   represent = lambda v: \
                                    float_represent(v, precision=2)
                                   ),
                             # These comments do *not* pull through to an Inventory's Items or a Request's Items
                             s3_comments(),
                             *s3_meta_fields())

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

        supply_item_represent = supply_ItemRepresent(show_link=True)

        # Reusable Field
        supply_item_id = S3ReusableField("item_id", table, sortby="name", # 'item_id' for backwards-compatibility
                    requires = IS_ONE_OF(db, "supply_item.id",
                                         supply_item_represent,
                                         sort=True),
                    represent = supply_item_represent,
                    label = T("Item"),
                    widget = S3AutocompleteWidget("supply", "item"),
                    comment=S3AddResourceLink(c="supply",
                                              f="item",
                                              label=ADD_ITEM,
                                              title=T("Item"),
                                              tooltip=T("Type the name of an existing catalog item OR Click 'Add New Item' to add an item which is not in the catalog.")),
                    ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Item Search Method
        #
        search_widgets = [
            S3SearchSimpleWidget(
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
                cols = 1
            ),
            ]
        report_options = Storage(
            search=search_widgets,
            defaults=Storage(rows="item.name",
                             cols="item.item_category_id",
                             fact="count:item.brand_id",
                             ),
            hide_comments=True,
        )
        search_method = S3Search(simple=(),
                                 advanced=search_widgets)

        configure(tablename,
                  deduplicate = self.supply_item_duplicate,
                  onaccept = self.supply_item_onaccept,
                  orderby = table.name,
                  search_method = search_method,
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
        add_component("inv_track_item", supply_item="item_id")

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
        # Item Categories are also Catalog specific
        #
        tablename = "supply_catalog_item"
        table = define_table(tablename,
                             catalog_id(),
                             item_category_id(
                                script = item_category_script
                                ),
                             supply_item_id(script=None), # No Item Pack Filter
                             s3_comments(), # These comments do *not* pull through to an Inventory's Items or a Request's Items
                             *s3_meta_fields())

        # CRUD strings
        ADD_ITEM = T("Add Item to Catalog")
        crud_strings[tablename] = Storage(
            title_create = T("Add Catalog Item"),
            title_display = T("Item Catalog Details"),
            title_list = T("Catalog Items"),
            title_update = T("Edit Catalog Item"),
            title_upload = T("Import Catalog Items"),
            title_search = T("Search Catalog Items"),
            subtitle_create = ADD_ITEM,
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

        # Search Method
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

        search_method = S3Search(
            simple=(catalog_item_search_simple_widget("simple")),
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
                         represent = item_category_represent_nocodes,
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
                  deduplicate = self.supply_catalog_item_duplicate,
                  search_method = search_method,
                  )

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
                             Field("quantity", "double", notnull=True,
                                   default = 1,
                                   label = T("Quantity"),
                                   represent = lambda v: \
                                    float_represent(v, precision=2)
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
                    # will be populated by S3OptionsFilter
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
                    script = '''
S3OptionsFilter({
 'triggerName':'item_id',
 'targetName':'item_pack_id',
 'lookupPrefix':'supply',
 'lookupResource':'item_pack',
 'msgNoRecords':i18n.no_packs,
 'fncPrep':S3.supply.fncPrepItem,
 'fncRepresent':S3.supply.fncRepresentItem
})''',
                    ondelete = "RESTRICT")

        configure(tablename,
                  deduplicate = self.supply_item_pack_duplicate)

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
                                   represent = lambda v: \
                                    float_represent(v, precision=2)
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
                             Field("quantity", "double",
                                   label = T("Quantity"),
                                   comment = DIV(_class = "tooltip",
                                                 _title = "%s|%s" %
                                                       (T("Quantity"),
                                                        T("The number of Units of Measure of the Alternative Items which is equal to One Unit of Measure of the Item")
                                                       )
                                               ),
                                   default = 1,
                                   notnull=True,
                                   represent = lambda v: \
                                    float_represent(v, precision=2)
                                   ),
                             supply_item_id("alt_item_id", notnull=True),
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

        # =====================================================================
        # Item Super-Entity
        #
        # This super entity provides a common way to provide a foreign key to supply_item
        # - it allows searching/reporting across Item types easily.
        #
        item_types = Storage(
                            inv_inv_item = T("Warehouse Stock"),
                            inv_track_item = T("Order Item"),
                            proc_plan_item = T("Planned Procurement Item"),
                            )

        tablename = "supply_item_entity"
        table = self.super_entity(tablename, "item_entity_id", item_types,
                                  # @ToDo: Make Items Trackable?
                                  #super_link("track_id", "sit_trackable"),
                                  #location_id(),
                                  supply_item_id(),
                                  item_pack_id(),
                                  Field("quantity", "double", notnull=True,
                                        label = T("Quantity"),
                                        default = 1.0,
                                        ),
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
        search_method = S3Search(
            # Advanced Search only
            simple=(),
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
                  search_method = search_method)

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return Storage(
                supply_item_id = supply_item_id,
                supply_item_entity_id = item_id,
                supply_item_category_id = item_category_id,
                supply_item_pack_id = item_pack_id,
                supply_item_represent = supply_item_represent,
                supply_item_category_represent = item_category_represent,
                supply_item_pack_quantity = SupplyItemPackQuantity,
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
                supply_item_pack_quantity = lambda tablename: lambda row: 0,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def supply_item_add(quantity_1, pack_quantity_1,
                        quantity_2, pack_quantity_2):
        """
            Adds item quantities together, accounting for different pack
            quantities.
            Returned quantity according to pack_quantity_1

            Used by controllers/inv.py & modules/s3db/inv.py
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
    def item_represent(id):
        """
            Represent an item entity in option fields or list views
            - unused, we use VirtualField instead
            @ToDo: Migrate to S3Represent
        """

        if not id:
            return current.messages["NONE"]

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
        elif instance_type == "inv_track_item":
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

    # ---------------------------------------------------------------------
    @staticmethod
    def item_pack_represent(id, row=None):
        """
            Represent an Item Pack
            @ToDo: Migrate to S3Represent
        """

        if row:
            # @ToDo: Optimised query where we don't need to do the join
            id = row.id
        elif not id:
            return current.messages["NONE"]

        db = current.db
        table = db.supply_item_pack
        query = (table.id == id) & \
                (table.item_id == db.supply_item.id)
        record = db(query).select(table.name,
                                  table.quantity,
                                  db.supply_item.um,
                                  limitby = (0, 1)).first()
        try:
            if record.supply_item_pack.quantity == 1:
                return record.supply_item_pack.name
            else:
                return "%s (%s x %s)" % (record.supply_item_pack.name,
                                         record.supply_item_pack.quantity,
                                         record.supply_item.um)
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def supply_item_duplicate(item):
        """
            Callback function used to look for duplicates during
            the import process

            @param item: the S3ImportItem to check
        """

        if item.tablename == "supply_item":
            db = current.db
            data = item.data
            table = item.table
            query = (table.deleted != True)
            code = data.get("code", None)
            if code:
                # Same Code => definitely duplicate
                query = query & (table.code.lower() == code.lower())
                row = db(query).select(table.id,
                                       limitby=(0, 1)).first()
                if row:
                    item.id = row.id
                    item.method = item.METHOD.UPDATE
                    return

            name = data.get("name", None)
            um = data.get("um", None)
            if not um:
                # Try to extract UM from Name
                name, um = item_um_from_name(name)
            if name:
                query = query & (table.name.lower() == name.lower())
            if um:
                query = query & (table.um.lower() == um.lower())
            catalog_id = data.get("catalog_id", None)
            if catalog_id:
                query = query & (table.catalog_id == catalog_id)

            row = db(query).select(table.id,
                                   limitby=(0, 1)).first()
            if row:
                item.id = row.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def supply_item_category_duplicate(item):
        """
            Callback function used to look for duplicates during
            the import process

            @param item: the S3ImportItem to check
        """

        if item.tablename == "supply_item_category":
            data = item.data
            table = item.table
            query = (table.deleted != True)
            name = data.get("name", None)
            if name:
                query = query & (table.name.lower() == name.lower())
            code = data.get("code", None)
            if code:
                query = query & (table.code.lower() == code.lower())
            catalog_id = data.get("catalog_id", None)
            if catalog_id:
                query = query & (table.catalog_id == catalog_id)
            parent_category_id = data.get("parent_category_id", None)
            if parent_category_id:
                query = query & (table.parent_category_id == parent_category_id)
            row = current.db(query).select(table.id,
                                           limitby=(0, 1)).first()
            if row:
                item.id = row.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def supply_catalog_item_duplicate(item):
        """
            Callback function used to look for duplicates during
            the import process

            @param item: the S3ImportItem to check
        """

        if item.tablename == "supply_catalog_item":
            data = item.data
            table = item.table
            query = (table.deleted != True)
            item_id = data.get("item_id", None)
            if item_id:
                query = query & (table.item_id == item_id)
            catalog_id = data.get("catalog_id", None)
            if catalog_id:
                query = query & (table.catalog_id == catalog_id)
            item_category_id = data.get("item_category_id", None)
            if item_category_id:
                query = query & (table.item_category_id == item_category_id)
            row = current.db(query).select(table.id,
                                           limitby=(0, 1)).first()
            if row:
                item.id = row.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def supply_item_pack_duplicate(item):
        """
            Callback function used to look for duplicates during
            the import process

            @param item: the S3ImportItem to check
        """

        if item.tablename == "supply_item_pack":
            data = item.data
            table = item.table
            query = (table.deleted != True)
            name = data.get("name", None)
            if name:
                query = query & (table.name.lower() == name.lower())
            item_id = data.get("item_id", None)
            if item_id:
                query = query & (table.item_id == item_id)
            quantity = data.get("quantity", None)
            if quantity:
                query = query & (table.quantity == quantity)
            row = current.db(query).select(table.id,
                                           limitby=(0, 1)).first()
            if row:
                item.id = row.id
                item.method = item.METHOD.UPDATE

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
class S3SupplyDistributionModel(S3Model):
    """
        Supply Distribution Model
        - depends on Stats module
    """

    names = ["supply_distribution_item",
             "supply_distribution",
             ]

    def model(self):

        if not current.deployment_settings.has_module("stats"):
            # Distribution Model needs Stats module enabling
            return dict()

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Distribution Item
        #
        tablename = "supply_distribution_item"
        table = define_table(tablename,
                             super_link("parameter_id", "stats_parameter"),
                             self.supply_item_entity_id,
                             self.supply_item_id(ondelete = "RESTRICT",
                                                 required = True),
                             Field("name", length=128, unique=True,
                                   requires = IS_NOT_IN_DB(db,
                                                           "supply_distribution_item.name")),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_ITEM = T("Add Distribution Item")
        crud_strings[tablename] = Storage(
            title_create = ADD_ITEM,
            title_display = T("Distribution Item"),
            title_list = T("Distribution Items"),
            title_update = T("Edit Distribution Item"),
            title_search = T("Search Distribution Items"),
            subtitle_create = T("Add New Distribution Item"),
            label_list_button = T("List Distribution Items"),
            label_create_button = ADD_ITEM,
            msg_record_created = T("Distribution Item Added"),
            msg_record_modified = T("Distribution Item Updated"),
            msg_record_deleted = T("Distribution Item Deleted"),
            msg_list_empty = T("No Distribution Items Found")
        )

        # Resource Configuration
        configure(tablename,
                  super_entity = ("stats_parameter", "supply_item_entity"),
                  onaccept=self.supply_distribution_item_onaccept,
                  )

        # ---------------------------------------------------------------------
        # Distribution
        #
        tablename = "supply_distribution"
        table = define_table(tablename,
                             # Link Fields
                             # populated automatically
                             self.project_project_id(readable=False,
                                                     writable=False),
                             self.project_location_id(comment=None),
                             # Instance
                             super_link("data_id", "stats_data"),
                             # This is a component, so needs to be a super_link
                             # - can't override field name, ondelete or requires
                             super_link("parameter_id", "stats_parameter",
                                        label = T("Item"),
                                        instance_types = ["supply_distribution_item"],
                                        represent = S3Represent(lookup="stats_parameter"),
                                        readable = True,
                                        writable = True,
                                        empty = False,
                                        comment = S3AddResourceLink(c="supply",
                                                                    f="distribution_item",
                                                                    vars = dict(child = "parameter_id"),
                                                                    title=ADD_ITEM),
                                        ),
                             # Populated automatically from project_location
                             self.gis_location_id(readable = False,
                                                  writable = False),
                             Field("value", "double",
                                   label = T("Quantity"),
                                   requires = IS_INT_IN_RANGE(0, 99999999),
                                   represent = lambda v: \
                                    IS_INT_AMOUNT.represent(v)),
                             s3_date("date",
                                     label = T("Start Date"),
                                     #empty = False,
                                     ),
                             s3_date("end_date",
                                     label = T("End Date"),
                                     #empty = False,
                                     ),
                             #self.stats_source_id(),
                             s3_comments(),
                             *s3_meta_fields())

        # Virtual fields
        table.year = Field.Lazy(self.supply_distribution_year)

        # CRUD Strings
        ADD_DIST = T("Add Distribution")
        crud_strings[tablename] = Storage(
            title_create = ADD_DIST,
            title_display = T("Distribution Details"),
            title_list = T("Distributions"),
            title_update = T("Edit Distribution"),
            title_search = T("Search Distributions"),
            title_report = T("Distribution Report"),
            subtitle_create = T("Add New Distribution"),
            label_list_button = T("List Distributions"),
            label_create_button = ADD_DIST,
            msg_record_created = T("Distribution Added"),
            msg_record_modified = T("Distribution Updated"),
            msg_record_deleted = T("Distribution Deleted"),
            msg_list_empty = T("No Distributions Found")
        )

        # Resource Configuration
        # ---------------------------------------------------------------------
        def year_options():
            """
                returns a dict of the options for the year virtual field
                used by the search widget

                orderby needed for postgres
            """

            ptable = db.project_project
            pbtable = db.supply_distribution
            pquery = (ptable.deleted == False)
            pbquery = (pbtable.deleted == False)
            pmin = ptable.start_date.min()
            pbmin = pbtable.date.min()
            p_start_date_min = db(pquery).select(pmin,
                                                 orderby=pmin,
                                                 limitby=(0, 1)).first()[pmin]
            pb_date_min = db(pbquery).select(pbmin,
                                             orderby=pbmin,
                                             limitby=(0, 1)).first()[pbmin]
            if p_start_date_min and pb_date_min:
                start_year = min(p_start_date_min,
                                 pb_date_min).year
            else:
                start_year = (p_start_date_min and p_start_date_min.year) or \
                             (pb_date_min and pb_date_min.year)

            pmax = ptable.end_date.max()
            pbmax = pbtable.end_date.max()
            p_end_date_max = db(pquery).select(pmax,
                                               orderby=pmax,
                                               limitby=(0, 1)).first()[pmax]
            pb_end_date_max = db(pbquery).select(pbmax,
                                                 orderby=pbmax,
                                                 limitby=(0, 1)).first()[pbmax]
            if p_end_date_max and pb_end_date_max:
                end_year = max(p_end_date_max,
                               pb_end_date_max).year
            else:
                end_year = (p_end_date_max and p_end_date_max.year) or \
                           (pb_end_date_max and pb_end_date_max.year)

            if not start_year or not end_year:
                return {start_year:start_year} or {end_year:end_year}
            years = {}
            for year in xrange(start_year, end_year + 1):
                years[year] = year
            return years

        filter_widgets = [
            S3TextFilter([#"item_id$name",
                          "project_id$name",
                          "project_id$code",
                          "location_id",
                          "comments"
                          ],
                         label = T("Search Distributions"),
                         ),
            #S3OptionsFilter("project_id",
            #                label = T("Project"),
            #                cols = 3,
            #                widget="multiselect"
            #                ),
            S3OptionsFilter("project_id$organisation_id",
                            label = T("Lead Organisation"),
                            cols = 3,
                            widget="multiselect"
                            ),
            S3OptionsFilter("parameter_id",
                            label = T("Item"),
                            cols = 3,
                            widget="multiselect"
                            ),
            #S3OptionsFilter("year",
            #                label = T("Year"),
            #                cols = 3,
            #                widget="multiselect",
            #                options = year_options
            #                ),
            S3OptionsFilter("location_id$L1",
                            location_level="L1",
                            widget="multiselect"),
            S3OptionsFilter("project_id$partner.organisation_id",
                            label = T("Partners"),
                            widget="multiselect"),
            S3OptionsFilter("project_id$donor.organisation_id",
                            label = T("Donors"),
                            location_level="L1",
                            widget="multiselect")
            ]

        report_fields = ["project_location_id",
                         (T("Item"), "parameter_id"),
                         #"project_id",
                         (T("Year"), "year"),
                         #"project_id$hazard.name",
                         #"project_id$theme.name",
                         (current.messages.COUNTRY, "location_id$L0"),
                         "location_id$L1",
                         "location_id$L2",
                         "location_id$L3",
                         #"location_id$L4",
                         ]

        configure(tablename,
                  super_entity = "stats_data",
                  onaccept = self.supply_distribution_onaccept,
                  deduplicate = self.supply_distribution_deduplicate,
                  filter_widgets = filter_widgets,
                  report_options=Storage(
                    rows=report_fields,
                    cols=report_fields,
                    fact=report_fields + ["value"],
                    defaults=Storage(rows="location_id$L1",
                                     cols="parameter_id",
                                     # T("Projects")
                                     fact="sum(value)",
                                     totals=True
                                     ),
                    extra_fields = ["project_id",
                                    #"date",
                                    #"end_date"
                                    ]
                    )
                 )

        # Pass names back to global scope (s3.*)
        return dict()

    # ---------------------------------------------------------------------
    @staticmethod
    def supply_distribution_item_onaccept(form):
        """
            Update supply_distribution_item name from supply_item_id
        """

        db = current.db
        dtable = db.supply_distribution_item
        ltable = db.supply_item

        record_id = form.vars.id
        query = (dtable.id == record_id) & \
                (ltable.id == dtable.item_id)
        item = db(query).select(ltable.name,
                                limitby=(0, 1)).first()
        if item:
            db(dtable.id == record_id).update(name = item.name)
        return

    # ---------------------------------------------------------------------
    @staticmethod
    def supply_distribution_onaccept(form):
        """
            Update supply_distribution project & location from project_location_id
        """

        db = current.db
        dtable = db.supply_distribution
        ltable = db.project_location

        record_id = form.vars.id
        query = (dtable.id == record_id) & \
                (ltable.id == dtable.project_location_id)
        project_location = db(query).select(ltable.project_id,
                                            ltable.location_id,
                                            limitby=(0, 1)).first()
        if project_location:
            db(dtable.id == record_id).update(
                    project_id = project_location.project_id,
                    location_id = project_location.location_id
                )
        return

    # ---------------------------------------------------------------------
    @staticmethod
    def supply_distribution_deduplicate(item):
        """ Import item de-duplication """

        if item.tablename != "supply_distribution":
            return

        data = item.data
        if "parameter_id" in data and \
           "project_location_id" in data:
            # Match distribution by item and project_location
            table = item.table
            parameter_id = data.parameter_id
            project_location_id = data.project_location_id
            query = (table.parameter_id == parameter_id) & \
                    (table.project_location_id == project_location_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

    # ---------------------------------------------------------------------
    @staticmethod
    def supply_distribution_year(row):
        """ Virtual field for the supply_distribution table """

        if hasattr(row, "supply_distribution"):
            row = row.supply_distribution

        try:
            project_id = row.project_id
        except AttributeError:
            return []
        try:
            date = row.date
        except AttributeError:
            date = None
        try:
            end_date = row.end_date
        except AttributeError:
            end_date = None

        if not date or not end_date:
            table = current.s3db.project_project
            project = current.db(table.id == project_id) \
                             .select(table.start_date,
                                     table.end_date,
                                     limitby=(0, 1)).first()
            if project:
                if not date:
                    date = project.start_date
                if not end_date:
                    end_date = project.end_date

        if not date and not end_date:
            return []
        elif not end_date:
            return [date.year]
        elif not date:
            return [end_date.year]
        else:
            return list(xrange(date.year, end_date.year + 1))

# =============================================================================
class supply_ItemRepresent(S3Represent):
    """ Representation of Supply Items """

    def __init__(self,
                 translate=False,
                 show_link=False,
                 show_um=False,
                 multiple=False):

        self.show_um = show_um

        # Need a custom lookup to join with Brand
        self.lookup_rows = self.custom_lookup_rows
        fields = ["supply_item.id",
                  "supply_item.name",
                  "supply_item.model",
                  "supply_brand.name",
                  ]
        if show_um:
            fields.append("supply_item.um")

        super(supply_ItemRepresent,
              self).__init__(lookup="supply_item",
                             fields=fields,
                             show_link=show_link,
                             translate=translate,
                             multiple=multiple)

    # -------------------------------------------------------------------------
    def custom_lookup_rows(self, key, values, fields=[]):
        """
            Custom lookup method for item rows, does a
            left join with the brand. Parameters
            key and fields are not used, but are kept for API
            compatibility reasons.

            @param values: the organisation IDs
        """

        db = current.db
        itable = current.s3db.supply_item
        btable = db.supply_brand

        left = btable.on(btable.id == itable.brand_id)

        qty = len(values)
        if qty == 1:
            query = (itable.id == values[0])
            limitby = (0, 1)
        else:
            query = (itable.id.belongs(values))
            limitby = (0, qty)

        rows = db(query).select(*self.fields,
                                left=left,
                                limitby=limitby)
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a single Row

            @param row: the supply_item Row
        """

        name = row["supply_item.name"]
        model = row["supply_item.model"]
        brand = row["supply_brand.name"]

        fields = []
        if name:
            fields.append(name)
        if model:
            fields.append(model)
        if brand:
            fields.append(brand)
        name = " - ".join(fields)

        if self.show_um:
            um = row["supply_item.um"]
            if um:
                name = "%s (%s)" % (name, um)
        return s3_unicode(name)

# =============================================================================
class supply_ItemCategoryRepresent(S3Represent):
    """ Representation of Supply Item Categories """

    def __init__(self,
                 translate=False,
                 show_link=False,
                 use_code=True,
                 multiple=False):

        self.use_code = use_code

        # Need a custom lookup to join with Parent/Catalog
        self.lookup_rows = self.custom_lookup_rows
        fields = ["supply_item_category.id",
                  "supply_item_category.name",
                  # Always-included since used as fallback if no name
                  "supply_item_category.code",
                  "supply_catalog.name",
                  "supply_parent_item_category.name",
                  "supply_grandparent_item_category.name",
                  "supply_grandparent_item_category.parent_item_category_id",
                  ]

        super(supply_ItemCategoryRepresent,
              self).__init__(lookup="supply_item_category",
                             fields=fields,
                             show_link=show_link,
                             translate=translate,
                             multiple=multiple)

    # -------------------------------------------------------------------------
    def custom_lookup_rows(self, key, values, fields=[]):
        """
            Custom lookup method for item category rows, does a
            left join with the parent category. Parameters
            key and fields are not used, but are kept for API
            compatibility reasons.

            @param values: the organisation IDs
        """

        db = current.db
        table = current.s3db.supply_item_category
        ctable = db.supply_catalog
        ptable = db.supply_item_category.with_alias("supply_parent_item_category")
        gtable = db.supply_item_category.with_alias("supply_grandparent_item_category")

        left = [ctable.on(ctable.id == table.catalog_id),
                ptable.on(ptable.id == table.parent_item_category_id),
                gtable.on(gtable.id == ptable.parent_item_category_id),
                ]

        qty = len(values)
        if qty == 1:
            query = (table.id == values[0])
            limitby = (0, 1)
        else:
            query = (table.id.belongs(values))
            limitby = (0, qty)

        rows = db(query).select(*self.fields,
                                left=left,
                                limitby=limitby)
        self.queries += 1
        return rows

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a single Row

            @param row: the supply_item_category Row
        """

        use_code = self.use_code

        name = row["supply_item_category.name"]
        code = row["supply_item_category.code"]
        catalog = row["supply_catalog.name"]
        parent = row["supply_parent_item_category.name"]

        if use_code:
            name = code
        elif not name:
            name = code

        if parent:
            if use_code:
                # Compact format
                joiner = "-"
            else:
                joiner = " - "
            name = "%s%s%s" % (name, joiner, parent)
            grandparent = row["supply_grandparent_item_category.name"]
            if grandparent:
                name = "%s%s%s" % (name, joiner, grandparent)
                # Check for Great-grandparent
                # Trade-off "all in 1 row" vs "too many joins"
                greatgrandparent = row["supply_grandparent_item_category.parent_item_category_id"]
                if greatgrandparent:
                    # Assume no more than 6 levels of interest
                    db = current.db
                    table = current.s3db.supply_item_category
                    ptable = db.supply_item_category.with_alias("supply_parent_item_category")
                    gtable = db.supply_item_category.with_alias("supply_grandparent_item_category")
                    left = [ptable.on(ptable.id == table.parent_item_category_id),
                            gtable.on(gtable.id == ptable.parent_item_category_id),
                            ]
                    query = (table.id == greatgrandparent)
                    fields = [table.name,
                              table.code,
                              ptable.name,
                              ptable.code,
                              gtable.name,
                              gtable.code,
                              ]
                    row = db(query).select(*fields,
                                           left=left,
                                           limitby=(0, 1)).first()
                    if row:
                        if use_code:
                            greatgrandparent = row["supply_item_category.code"]
                            greatgreatgrandparent = row["supply_parent_item_category.code"]
                        else:
                            greatgrandparent = row["supply_item_category.name"] or row["supply_item_category.code"]
                            greatgreatgrandparent = row["supply_parent_item_category.name"] or row["supply_parent_item_category.code"]
                        name = "%s%s%s" % (name, joiner, greatgrandparent)
                        if greatgreatgrandparent:
                            name = "%s%s%s" % (name, joiner, greatgreatgrandparent)
                            if use_code:
                                greatgreatgreatgrandparent = row["supply_grandparent_item_category.code"]
                            else:
                                greatgreatgreatgrandparent = row["supply_grandparent_item_category.name"] or row["supply_grandparent_item_category.code"]
                            if greatgreatgreatgrandparent:
                                name = "%s%s%s" % (name, joiner, greatgreatgreatgrandparent)

        if catalog:
            name = "%s > %s" % (catalog, name)

        return s3_unicode(name)

# =============================================================================
def item_um_from_name(name):
    """
        Retrieve the Unit of Measure from a name
    """

    for um_pattern in um_patterns:
        m = re.search(um_pattern, name)
        if m:
            um = m.group(1).strip()
            # Rename name from um
            name = re.sub(um_pattern, "", name)
            # Remove trailing , & wh sp
            name = re.sub("(,)$", "", name).strip()
            return (name, um)

    return (name, None)

# =============================================================================
def supply_catalog_rheader(r):
    """ Resource Header for Catalogs """

    if r.representation == "html":
        catalog = r.record
        if catalog:
            T = current.T
            tabs = [(T("Edit Details"), None),
                    (T("Categories"), "item_category"),
                    (T("Items"), "catalog_item"),
                    ]
            rheader_tabs = s3_rheader_tabs(r, tabs)

            table = r.table

            rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                                   catalog.name,
                                   ),
                                TR(TH("%s: " % table.organisation_id.label),
                                   table.organisation_id.represent(catalog.organisation_id),
                                   ),
                                ),
                          rheader_tabs
                          )
            return rheader
    return None

# =============================================================================
def supply_item_rheader(r):
    """ Resource Header for Items """

    if r.representation == "html":
        item = r.record
        if item:

            T = current.T

            tabs = [(T("Edit Details"), None),
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
                                    item.model or current.messages["NONE"],
                                  ),
                               ),
                          rheader_tabs
                         )
            return rheader
    return None

# =============================================================================
class SupplyItemPackQuantity(object):
    """ Virtual Field for pack_quantity """

    def __init__(self, tablename):
        self.tablename = tablename

    def __call__(self, row):

        default = 0

        tablename = self.tablename
        if hasattr(row, tablename):
            row = object.__getattribute__(row, tablename)
        try:
            item_pack_id = row.item_pack_id
        except AttributeError:
            return default
            
        if item_pack_id:
            return item_pack_id.quantity
        else:
            return default

# =============================================================================
def supply_item_entity_category(row):
    """ Virtual field: category """

    if hasattr(row, "supply_item_entity"):
        row = row.supply_item_entity
    else:
        return None
    try:
        item_id = row.item_id
    except AttributeError:
        return None

    table = current.s3db.supply_item
    query = (table.id == item_id)
    
    record = current.db(query).select(table.item_category_id,
                                      limitby=(0, 1)).first()
    if record:
        return table.item_category_id.represent(record.item_category_id)
    else:
        return current.messages["NONE"]

# -------------------------------------------------------------------------
def supply_item_entity_country(row):
    """ Virtual field: country """
    
    if hasattr(row, "supply_item_entity"):
        row = row.supply_item_entity
    else:
        return None
        
    s3db = current.s3db
    etable = s3db.supply_item_entity

    ekey = etable._id.name
    
    try:
        instance_type = row.instance_type
    except AttributeError:
        return None
    try:
        entity_id = row[ekey]
    except AttributeError:
        return None
    
    itable = s3db[instance_type]
    ltable = s3db.gis_location
    
    if instance_type == "inv_inv_item":
        
        stable = s3db.org_site
        query = (itable[ekey] == entity_id) & \
                (stable.site_id == itable.site_id) & \
                (ltable.id == stable.location_id)
        record = current.db(query).select(ltable.L0,
                                          limitby=(0, 1)).first()
            
    elif instance_type == "inv_track_item":
        
        rtable = s3db.inv_recv
        stable = s3db.org_site
        query = (itable[ekey] == entity_id) & \
                (rtable.id == itable.recv_id) & \
                (stable.site_id == rtable.site_id) & \
                (ltable.id == stable.location_id)
        record = current.db(query).select(ltable.L0,
                                          limitby=(0, 1)).first()
            
    elif instance_type == "proc_plan_item":
        
        ptable = s3db.proc_plan
        stable = s3db.org_site
        query = (itable[ekey] == entity_id) & \
                (ptable.id == itable.plan_id) & \
                (stable.site_id == ptable.site_id) & \
                (ltable.id == stable.location_id)
        record = current.db(query).select(ltable.L0,
                                          limitby=(0, 1)).first()
           
    else:
        # @ToDo: Assets and req_items
        record = None

    if record:
        return record.L0 or current.T("Unknown")
    else:
        return current.messages["NONE"]

# -------------------------------------------------------------------------
def supply_item_entity_organisation(row):
    """ Virtual field: organisation """

    if hasattr(row, "supply_item_entity"):
        row = row.supply_item_entity
    else:
        return None

    s3db = current.s3db
    etable = s3db.supply_item_entity

    ekey = etable._id.name

    try:
        instance_type = row.instance_type
    except AttributeError:
        return None
    try:
        entity_id = row[ekey]
    except AttributeError:
        return None

    organisation_represent = s3db.org_OrganisationRepresent(acronym=False)
    itable = s3db[instance_type]
    
    if instance_type == "inv_inv_item":

        stable = s3db.org_site
        query = (itable[ekey] == entity_id) & \
                (stable.site_id == itable.site_id)
        record = current.db(query).select(stable.organisation_id,
                                          limitby=(0, 1)).first()
                                          
    elif instance_type == "proc_plan_item":
        
        rtable = s3db.proc_plan
        stable = s3db.org_site
        query = (itable[ekey] == entity_id) & \
                (rtable.id == itable.plan_id) & \
                (stable.site_id == rtable.site_id)
        record = current.db(query).select(stable.organisation_id,
                                          limitby=(0, 1)).first()
                                          
    elif instance_type == "inv_track_item":
        
        rtable = s3db.inv_recv
        stable = s3db.org_site
        query = (itable[ekey] == entity_id) & \
                (rtable.id == itable.recv_id) & \
                (stable.site_id == rtable.site_id)
        record = current.db(query).select(stable.organisation_id,
                                          limitby=(0, 1)).first()
                                          
    else:
        # @ToDo: Assets and req_items
        record = None

    if record:
        return organisation_represent(record.organisation_id)
    else:
        return current.messages["NONE"]

# -------------------------------------------------------------------------
def supply_item_entity_contacts(row):
    """ Virtual field: contacts (site_id) """
    
    if hasattr(row, "supply_item_entity"):
        row = row.supply_item_entity
    else:
        return None

    db = current.db
    s3db = current.s3db
    etable = s3db.supply_item_entity

    ekey = etable._id.name

    try:
        instance_type = row.instance_type
    except AttributeError:
        return None
    try:
        entity_id = row[ekey]
    except AttributeError:
        return None

    itable = s3db[instance_type]

    if instance_type == "inv_inv_item":

        query = (itable[ekey] == entity_id)
        record = db(query).select(itable.site_id,
                                  limitby=(0, 1)).first()
                                          
    elif instance_type == "inv_track_item":
        
        rtable = s3db.inv_recv
        query = (itable[ekey] == entity_id) & \
                (rtable.id == itable.recv_id)
        record = db(query).select(rtable.site_id,
                                  limitby=(0, 1)).first()
                                  
    elif instance_type == "proc_plan_item":
        
        ptable = s3db.proc_plan
        query = (itable[ekey] == entity_id) & \
                (ptable.id == itable.plan_id)
        record = db(query).select(ptable.site_id,
                                  limitby=(0, 1)).first()
    else:
        # @ToDo: Assets and req_items
        record = None

    default = current.messages["NONE"]

    if not record:
        return default

    otable = s3db.org_office
    query = (otable.site_id == record.site_id)
    office = db(query).select(otable.id,
                              otable.comments,
                              limitby=(0, 1)).first()

    if office:

        if current.request.extension in ("xls", "pdf"):
            if office.comments:
                return office.comments
            else:
                return default
                
        elif office.comments:
            comments = s3_comments_represent(office.comments,
                                             show_link=False)
        else:
            comments = default
            
        return A(comments,
                 _href = URL(f="office", args = [office.id]))
                 
    else:
        return default
                                      

# -------------------------------------------------------------------------
def supply_item_entity_status(row):
    """ Virtual field: status """
    
    if hasattr(row, "supply_item_entity"):
        row = row.supply_item_entity
    else:
        return None

    db = current.db
    s3db = current.s3db
    etable = s3db.supply_item_entity

    ekey = etable._id.name

    try:
        instance_type = row.instance_type
    except AttributeError:
        return None
    try:
        entity_id = row[ekey]
    except AttributeError:
        return None

    itable = s3db[instance_type]

    status = None
    
    if instance_type == "inv_inv_item":
        
        query = (itable[ekey] == entity_id)
        record = current.db(query).select(itable.expiry_date,
                                          limitby=(0, 1)).first()
        if record:
            T = current.T
            if record.expiry_date:
                status = T("Stock Expires %(date)s") % \
                          dict(date=record.expiry_date)
            else:
                status = T("In Stock")
                
    elif instance_type == "proc_plan_item":


        rtable = s3db.proc_plan
        query = (itable[ekey] == entity_id) & \
                (rtable.id == itable.plan_id)
        record = current.db(query).select(rtable.eta,
                                          limitby=(0, 1)).first()
        if record:
            T = current.T
            if record.eta:
                status = T("Planned %(date)s") % dict(date=record.eta)
            else:
                status = T("Planned Procurement")
                
    elif instance_type == "inv_track_item":
        
        rtable = s3db.inv_recv
        query = (itable[ekey] == entity_id) & \
                (rtable.id == itable.send_inv_item_id)
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
        return current.messages["NONE"]

    return status or current.messages["NONE"]

# =============================================================================
def supply_item_controller():
    """ RESTful CRUD controller """

    s3 = current.response.s3
    s3db = current.s3db

    def prep(r):
        if r.component:
            if r.component_name == "inv_item":
                # Inventory Items need proper accountability so are edited through inv_adj
                s3db.configure("inv_inv_item",
                               listadd=False,
                               deletable=False)
                # Filter to just item packs for this Item
                inv_item_pack_requires = IS_ONE_OF(current.db,
                                                   "supply_item_pack.id",
                                                   s3db.supply_item_pack_represent,
                                                   sort=True,
                                                   filterby = "item_id",
                                                   filter_opts = [r.record.id],
                                                   )
                s3db.inv_inv_item.item_pack_id.requires = inv_item_pack_requires
            elif r.component_name == "req_item":
                # This is a report not a workflow
                s3db.configure("req_req_item",
                               listadd=False,
                               deletable=False)

        # Needs better workflow as no way to add the Kit Items
        # else:
            # caller = current.request.get_vars.get("caller", None)
            # if caller == "inv_kit_item_id":
                # field = r.table.kit
                # field.default = True
                # field.readable = field.writable = False

        return True
    s3.prep = prep

    return current.rest_controller("supply", "item",
                                   rheader=s3db.supply_item_rheader)

# =============================================================================
def supply_item_entity_controller():
    """
        RESTful CRUD controller
        - consolidated report of inv_item, recv_item & proc_plan_item
        @ToDo: Migrate JS to Static as part of migrating this to an S3Search Widget
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

    table.category = Field.Lazy(supply_item_entity_category)
    table.country = Field.Lazy(supply_item_entity_country)
    table.organisation = Field.Lazy(supply_item_entity_organisation)
    table.contacts = Field.Lazy(supply_item_entity_contacts)
    table.status = Field.Lazy(supply_item_entity_status)

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
                                 ],
                   extra_fields = ["instance_type"],
                  )

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
            ltable = s3db.gis_location
            fields = [ltable.L0,
                      #table.name,
                      otable.name]
            query = (table.deleted == False) & \
                    (table.organisation_id == otable.id) & \
                    (ltable.id == table.location_id)
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
