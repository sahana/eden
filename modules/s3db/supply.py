# -*- coding: utf-8 -*-

""" Sahana Eden Supply Model

    @copyright: 2009-2014 (c) Sahana Software Foundation
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

__all__ = ("S3SupplyModel",
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
           "supply_get_shipping_code",
           )

import re

from gluon import *
try:
    from gluon.dal.objects import Row
except ImportError:
    # old web2py
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

    names = ("supply_brand",
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
             )

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        s3 = current.response.s3
        settings = current.deployment_settings

        # Shortcuts
        add_components = self.add_components
        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        float_represent = IS_FLOAT_AMOUNT.represent

        NONE = current.messages["NONE"]

        format = auth.permission.format
        if format == "html":
            i18n = {"in_inv": T("in Stock"),
                    "no_packs": T("No Packs for Item"),
                    }
            s3.js_global.append('''i18n.in_inv="%s"''' % i18n["in_inv"])
            s3.js_global.append('''i18n.no_packs="%s"''' % i18n["no_packs"])
            
        # =====================================================================
        # Brand
        #
        tablename = "supply_brand"
        define_table(tablename,
                     Field("name", length=128, notnull=True, unique=True,
                           label = T("Name"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_BRAND = T("Create Brand")
        crud_strings[tablename] = Storage(
            label_create = ADD_BRAND,
            title_display = T("Brand Details"),
            title_list = T("Brands"),
            title_update = T("Edit Brand"),
            label_list_button = T("List Brands"),
            label_delete_button = T("Delete Brand"),
            msg_record_created = T("Brand added"),
            msg_record_modified = T("Brand updated"),
            msg_record_deleted = T("Brand deleted"),
            msg_list_empty = T("No Brands currently registered"))

        # Reusable Field
        represent = S3Represent(lookup=tablename)
        brand_id = S3ReusableField("brand_id", "reference %s" % tablename,
            label = T("Brand"),
            ondelete = "RESTRICT",
            represent = represent,
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "supply_brand.id",
                                  represent,
                                  sort=True)
                        ),
            sortby = "name",
            comment = S3AddResourceLink(c="supply", f="brand",
                                        label=ADD_BRAND,
                                        title=T("Brand"),
                                        tooltip=T("The list of Brands are maintained by the Administrators.")),
            )

        # =====================================================================
        # Catalog (of Items)
        #
        tablename = "supply_catalog"
        define_table(tablename,
                     Field("name", length=128, notnull=True, unique=True,
                           label = T("Name"),
                           ),
                     self.org_organisation_id(),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_CATALOG = T("Create Catalog")
        crud_strings[tablename] = Storage(
            label_create = ADD_CATALOG,
            title_display = T("Catalog Details"),
            title_list = T("Catalogs"),
            title_update = T("Edit Catalog"),
            label_list_button = T("List Catalogs"),
            label_delete_button = T("Delete Catalog"),
            msg_record_created = T("Catalog added"),
            msg_record_modified = T("Catalog updated"),
            msg_record_deleted = T("Catalog deleted"),
            msg_list_empty = T("No Catalogs currently registered"))

        # Reusable Field
        represent = S3Represent(lookup=tablename)
        catalog_id = S3ReusableField("catalog_id", "reference %s" % tablename,
            default = 1,
            label = T("Catalog"),
            ondelete = "RESTRICT",
            represent = represent,
            requires = IS_EMPTY_OR(
                        IS_ONE_OF(db, "supply_catalog.id",
                                  represent,
                                  sort=True,
                                  # Restrict to catalogs the user can update
                                  updateable=True,
                                  )),
            sortby = "name",
            comment=S3AddResourceLink(c="supply",
                                      f="catalog",
                                      label=ADD_CATALOG,
                                      title=T("Catalog"),
                                      tooltip=T("The list of Catalogs are maintained by the Administrators.")),
            )

        # Components
        add_components(tablename,
                       # Categories
                       supply_item_category = "catalog_id",
                       # Catalog Items
                       supply_catalog_item = "catalog_id",
                       )

        # =====================================================================
        # Item Category
        #
        asset = settings.has_module("asset")
        vehicle = settings.has_module("vehicle")

        item_category_represent = supply_ItemCategoryRepresent()
        item_category_represent_nocodes = \
            supply_ItemCategoryRepresent(use_code=False)

        if format == "xls":
            parent_represent = item_category_represent_nocodes
        else:
            parent_represent = item_category_represent

        tablename = "supply_item_category"
        define_table(tablename,
                     catalog_id(),
                     #Field("level", "integer"),
                     Field("parent_item_category_id",
                           "reference supply_item_category",
                           label = T("Parent"),
                           represent = parent_represent,
                           ondelete = "RESTRICT",
                           ),
                     Field("code", length=16,
                           label = T("Code"),
                           #required = True,
                           ),
                     Field("name", length=128,
                           label = T("Name"),
                           ),
                     Field("can_be_asset", "boolean",
                           default=True,
                           readable=asset,
                           writable=asset,
                           represent = s3_yes_no_represent,
                           label=T("Items in Category can be Assets"),
                           ),
                     Field("is_vehicle", "boolean",
                           default=False,
                           readable=vehicle,
                           writable=vehicle,
                           represent = s3_yes_no_represent,
                           label=T("Items in Category are Vehicles"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_ITEM_CATEGORY = T("Create Item Category")
        crud_strings[tablename] = Storage(
            label_create = ADD_ITEM_CATEGORY,
            title_display = T("Item Category Details"),
            title_list = T("Item Categories"),
            title_update = T("Edit Item Category"),
            label_list_button = T("List Item Categories"),
            label_delete_button = T("Delete Item Category"),
            msg_record_created = T("Item Category added"),
            msg_record_modified = T("Item Category updated"),
            msg_record_deleted = T("Item Category deleted"),
            msg_list_empty = T("No Item Categories currently registered"))

        # Reusable Field
        item_category_requires = IS_EMPTY_OR(
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

        # @todo: make lazy_table
        table = db[tablename]
        table.parent_item_category_id.requires = item_category_requires

        item_category_id = S3ReusableField("item_category_id", "reference %s" % tablename,
                                           comment = item_category_comment,
                                           label = T("Category"),
                                           ondelete = "RESTRICT",
                                           represent = item_category_represent,
                                           requires = item_category_requires,
                                           sortby = "name",
                                           )
        item_category_script = '''
$.filterOptionsS3({
 'trigger':'catalog_id',
 'target':'item_category_id',
 'lookupPrefix':'supply',
 'lookupResource':'item_category',
})'''

        # Components
        add_components(tablename,
                       # Child categories
                       supply_item_category = "parent_item_category_id",
                       )

        configure(tablename,
                  deduplicate = self.supply_item_category_duplicate,
                  onvalidation = self.supply_item_category_onvalidate,
                  )

        # =====================================================================
        # Item
        #
        #  These are Template items
        #  Instances of these become Inventory Items & Request items
        #
        tablename = "supply_item"
        define_table(tablename,
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
                           default = False,
                           label = T("Kit?"),
                           represent = lambda opt: \
                                       (opt and [T("Yes")] or [NONE])[0],
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
        ADD_ITEM = T("Create Item")
        crud_strings[tablename] = Storage(
            label_create = ADD_ITEM,
            title_display = T("Item Details"),
            title_list = T("Items"),
            title_update = T("Edit Item"),
            label_list_button = T("List Items"),
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
        supply_item_id = S3ReusableField("item_id",
            "reference %s" % tablename, # 'item_id' for backwards-compatibility
            label = T("Item"),
            ondelete = "RESTRICT",
            represent = supply_item_represent,
            requires = IS_ONE_OF(db, "supply_item.id",
                                 supply_item_represent,
                                 sort=True),
            sortby = "name",
            widget = S3AutocompleteWidget("supply", "item"),
            comment=S3AddResourceLink(c="supply",
                                      f="item",
                                      label=ADD_ITEM,
                                      title=T("Item"),
                                      tooltip=T("Type the name of an existing catalog item OR Click 'Create Item' to add an item which is not in the catalog.")),
            )

        # ---------------------------------------------------------------------
        filter_widgets = [
            S3TextFilter(["code",
                          "name",
                          "model",
                          #"item_category_id$name",
                          "comments",
                          ],
                         label = T("Search"),
                         comment = T("Search for an item by its code, name, model and/or comment."),
                         #_class = "filter-search",
                         ),
            S3OptionsFilter("brand_id",
                            # @ToDo: Introspect need for header based on # records
                            #header = True,
                            #label = T("Brand"),
                            represent = "%(name)s",
                            widget = "multiselect",
                            ),
            S3OptionsFilter("year",
                            comment = T("Search for an item by Year of Manufacture."),
                            # @ToDo: Introspect need for header based on # records
                            #header = True,
                            label = T("Year"),
                            widget = "multiselect",
                            ),
            ]

        report_options = Storage(defaults=Storage(rows="name",
                                                  cols="item_category_id",
                                                  fact="count(brand_id)",
                                                  ),
                                 )

        # Default summary
        summary = [{"name": "addform",
                    "common": True,
                    "widgets": [{"method": "create"}],
                    },
                   {"name": "table",
                    "label": "Table",
                    "widgets": [{"method": "datatable"}]
                    },
                   {"name": "report",
                    "label": "Report",
                    "widgets": [{"method": "report",
                                 "ajax_init": True}]
                    },
                   ]

        configure(tablename,
                  deduplicate = self.supply_item_duplicate,
                  filter_widgets = filter_widgets,
                  onaccept = self.supply_item_onaccept,
                  orderby = "supply_item.name",
                  report_options = report_options,
                  summary = summary,
                  )

        # Components
        add_components(tablename,
                       # Catalog Items
                       supply_catalog_item = "item_id",
                       # Packs
                       supply_item_pack = "item_id",
                       # Inventory Items
                       inv_inv_item = "item_id",
                       # Order Items
                       inv_track_item = "item_id",
                       # Procurement Plan Items
                       proc_plan_item = "item_id",
                       # Request Items
                       req_req_item = "item_id",
                       # Supply Kit Items
                       supply_kit_item = "parent_item_id",
                       # Supply Kit Items (with link table)
                       #supply_item = {"name": "kit_item",
                       #               "link": "supply_kit_item",
                       #               "joinby": "parent_item_id",
                       #               "key": "item_id"
                       #               "actuate": "hide",
                       #               },
                       )

        # Optional components
        if settings.get_supply_use_alt_name():
            add_components(tablename,
                           # Alternative Items
                           supply_item_alt="item_id",
                          )

        # =====================================================================
        # Catalog Item
        #
        # This resource is used to link Items with Catalogs (n-to-n)
        # Item Categories are also Catalog specific
        #
        tablename = "supply_catalog_item"
        define_table(tablename,
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
            label_create = T("Create Catalog Item"),
            title_display = T("Item Catalog Details"),
            title_list = T("Catalog Items"),
            title_update = T("Edit Catalog Item"),
            title_upload = T("Import Catalog Items"),
            label_list_button = T("List Catalog Items"),
            label_delete_button = T("Delete Catalog Item"),
            msg_record_created = T("Catalog Item added"),
            msg_record_modified = T("Catalog Item updated"),
            msg_record_deleted = T("Catalog Item deleted"),
            msg_list_empty = T("No Catalog Items currently registered"),
            msg_match = T("Matching Catalog Items"),
            msg_no_match = T("No Matching Catalog Items")
            )

        # Filter Widgets
        filter_widgets = [
            S3TextFilter([#These lines are causing issues...very slow - perhaps broken
                          #"comments",
                          #"item_category_id$code", 
                          #"item_category_id$name",
                          #"item_id$brand_id$name",
                          #"item_category_id$parent_item_category_id$code"
                          #"item_category_id$parent_item_category_id$name"
                          "item_id$code",
                          "item_id$name",
                          "item_id$model",
                          "item_id$comments"
                         ],
                         label=T("Search"),
                         comment= T("Search for an item by its code, name, model and/or comment."),
                        ),
            S3OptionsFilter("catalog_id",
                            label=T("Catalog"),
                            comment=T("Search for an item by catalog."),
                            #represent ="%(name)s",
                            cols = 3,
                            hidden = True,
                           ),
            S3OptionsFilter("item_category_id",
                            label=T("Category"),
                            comment=T("Search for an item by category."),
                            represent = item_category_represent_nocodes,
                            cols = 3,
                            hidden = True,
                           ),
            S3OptionsFilter("item_id$brand_id",
                            label=T("Brand"),
                            comment=T("Search for an item by brand."),
                            #represent ="%(name)s",
                            cols = 3,
                            hidden = True,
                           ),
        ]

        configure(tablename,
                  deduplicate = self.supply_catalog_item_duplicate,
                  filter_widgets = filter_widgets,
                 )

        # =====================================================================
        # Item Pack
        #
        #  Items can be distributed in different containers
        #
        tablename = "supply_item_pack"
        define_table(tablename,
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
        ADD_ITEM_PACK = T("Create Item Pack")
        crud_strings[tablename] = Storage(
            label_create = ADD_ITEM_PACK,
            title_display = T("Item Pack Details"),
            title_list = T("Item Packs"),
            title_update = T("Edit Item Pack"),
            label_list_button = T("List Item Packs"),
            label_delete_button = T("Delete Item Pack"),
            msg_record_created = T("Item Pack added"),
            msg_record_modified = T("Item Pack updated"),
            msg_record_deleted = T("Item Pack deleted"),
            msg_list_empty = T("No Item Packs currently registered"))

        # ---------------------------------------------------------------------
        # Reusable Field
        item_pack_represent = self.item_pack_represent
        item_pack_id = S3ReusableField("item_pack_id", "reference %s" % tablename,
                    label = T("Pack"),
                    ondelete = "RESTRICT",
                    represent = item_pack_represent,
                    # Do not display any packs initially
                    # will be populated by filterOptionsS3
                    requires = IS_ONE_OF_EMPTY_SELECT(db,
                                         "supply_item_pack.id",
                                         item_pack_represent,
                                         sort=True,
                                         # @ToDo: Enforce "Required" for imports
                                         # @ToDo: Populate based on item_id in controller instead of IS_ONE_OF_EMPTY_SELECT
                                         # filterby = "item_id",
                                         # filter_opts = (....),
                                         ),
                    script = '''
$.filterOptionsS3({
 'trigger':'item_id',
 'target':'item_pack_id',
 'lookupPrefix':'supply',
 'lookupResource':'item_pack',
 'msgNoRecords':i18n.no_packs,
 'fncPrep':S3.supply.fncPrepItem,
 'fncRepresent':S3.supply.fncRepresentItem
})''',
                    sortby = "name",
                    #comment=S3AddResourceLink(c="supply",
                    #                          f="item_pack",
                    #                          label=ADD_ITEM_PACK,
                    #                          title=T("Item Packs"),
                    #                          tooltip=T("The way in which an item is normally distributed")),
                    )

        configure(tablename,
                  deduplicate = self.supply_item_pack_duplicate,
                  )

        # Components
        add_components(tablename,
                       # Inventory Items
                       inv_inv_item = "item_pack_id",
                       )

        # =====================================================================
        # Supply Kit Item Table
        #
        # For defining what items are in a kit

        tablename = "supply_kit_item"
        define_table(tablename,
                     supply_item_id("parent_item_id",
                                    label = T("Parent Item"),
                                    comment = None,
                                    ),
                     supply_item_id("item_id",
                                    label = T("Kit Item"),
                                    ),
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
        define_table(tablename,
                     supply_item_id(notnull=True),
                     Field("quantity", "double", notnull=True,
                           default = 1,
                           label = T("Quantity"),
                           represent = lambda v: \
                            float_represent(v, precision=2),
                           comment = DIV(_class = "tooltip",
                                         _title = "%s|%s" %
                                                  (T("Quantity"),
                                                   T("The number of Units of Measure of the Alternative Items which is equal to One Unit of Measure of the Item")
                                                  )
                                         ),
                           ),
                     supply_item_id("alt_item_id", notnull=True),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Alternative Item"),
            title_display = T("Alternative Item Details"),
            title_list = T("Alternative Items"),
            title_update = T("Edit Alternative Item"),
            label_list_button = T("List Alternative Items"),
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
        item_types = Storage(asset_asset = T("Asset"),
                             asset_item = T("Asset Item"),
                             inv_inv_item = T("Warehouse Stock"),
                             inv_track_item = T("Order Item"),
                             proc_plan_item = T("Planned Procurement Item"),
                             )

        tablename = "supply_item_entity"
        self.super_entity(tablename, "item_entity_id", item_types,
                          # @ToDo: Make Items Trackable?
                          #super_link("track_id", "sit_trackable"),
                          #location_id(),
                          supply_item_id(),
                          item_pack_id(),
                          Field("quantity", "double", notnull=True,
                                default = 1.0,
                                label = T("Quantity"),
                                ),
                          *s3_ownerstamp())

        # Reusable Field
        item_id = super_link("item_entity_id", "supply_item_entity",
                             #writable = True,
                             #readable = True,
                             #label = T("Status"),
                             #represent = item_represent,
                             # Comment these to use a Dropdown & not an Autocomplete
                             #widget = S3ItemAutocompleteWidget(),
                             #comment = DIV(_class="tooltip",
                             #              _title="%s|%s" % (T("Item"),
                             #                                current.messages.AUTOCOMPLETE_HELP))
                             )

        # Filter Widgets
        filter_widgets = [
            S3TextFilter(name="item_entity_search_text",
                         label=T("Search"),
                         comment=T("Search for an item by text."),
                         field=["item_id$name",
                                #"item_id$item_category_id$name",
                                #"site_id$name"
                                ]
                         ),
            S3OptionsFilter("item_id$item_category_id",
                            label=T("Code Share"),
                            comment=T("If none are selected, then all are searched."),
                            #represent ="%(name)s",
                            cols = 2,
                           ),
            #S3OptionsFilter("country",
            #                label=current.messages.COUNTRY,
            #                comment=T("If none are selected, then all are searched."),
            #                #represent ="%(name)s",
            #                cols = 2,
            #               ),
        ]
        
        # Configuration
        configure(tablename,
                  filter_widgets = filter_widgets,
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict(supply_item_id = supply_item_id,
                    supply_item_entity_id = item_id,
                    supply_item_category_id = item_category_id,
                    supply_item_pack_id = item_pack_id,
                    supply_item_represent = supply_item_represent,
                    supply_item_category_represent = item_category_represent,
                    supply_item_pack_quantity = SupplyItemPackQuantity,
                    supply_item_add = self.supply_item_add,
                    supply_item_pack_represent = item_pack_represent,
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

        return dict(supply_item_id = supply_item_id,
                    supply_item_entity_id = item_id,
                    supply_item_pack_id = item_pack_id,
                    supply_item_pack_quantity = lambda tablename: lambda row: 0,
                    )

    # -------------------------------------------------------------------------
    @staticmethod
    def supply_item_category_onvalidate(form):
        """
            Checks that either a Code OR a Name are entered
        """

        # If there is a tracking number check that it is unique within the org
        if not (form.vars.code or form.vars.name):
            errors = form.errors
            errors.code = errors.name = current.T("An Item Category must have a Code OR a Name.")

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

        data = item.data
        code = data.get("code")
        if code:
            # Same Code => definitely duplicate
            table = item.table
            query = (table.deleted != True)
            query = query & (table.code.lower() == code.lower())
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
                return
        else:
            name = data.get("name")
            if not name:
                # No way to match
                return
            um = data.get("um")
            if not um:
                # Try to extract UM from Name
                name, um = item_um_from_name(name)
            table = item.table
            query = (table.deleted != True)
            if name:
                query = query & (table.name.lower() == name.lower())
            if um:
                query = query & (table.um.lower() == um.lower())
            catalog_id = data.get("catalog_id")
            if catalog_id:
                query = query & (table.catalog_id == catalog_id)

            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def supply_item_category_duplicate(item):
        """
            Callback function used to look for duplicates during
            the import process

            @param item: the S3ImportItem to check
        """

        data = item.data
        table = item.table
        query = (table.deleted != True)
        name = data.get("name")
        if name:
            query = query & (table.name.lower() == name.lower())
        code = data.get("code")
        if code:
            query = query & (table.code.lower() == code.lower())
        catalog_id = data.get("catalog_id")
        if catalog_id:
            query = query & (table.catalog_id == catalog_id)
        parent_category_id = data.get("parent_category_id")
        if parent_category_id:
            query = query & (table.parent_category_id == parent_category_id)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def supply_catalog_item_duplicate(item):
        """
            Callback function used to look for duplicates during
            the import process

            @param item: the S3ImportItem to check
        """

        data = item.data
        table = item.table
        query = (table.deleted != True)
        item_id = data.get("item_id")
        if item_id:
            query = query & (table.item_id == item_id)
        catalog_id = data.get("catalog_id")
        if catalog_id:
            query = query & (table.catalog_id == catalog_id)
        item_category_id = data.get("item_category_id")
        if item_category_id:
            query = query & (table.item_category_id == item_category_id)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def supply_item_pack_duplicate(item):
        """
            Callback function used to look for duplicates during
            the import process

            @param item: the S3ImportItem to check
        """

        data = item.data
        table = item.table
        query = (table.deleted != True)
        name = data.get("name")
        if name:
            query = query & (table.name.lower() == name.lower())
        item_id = data.get("item_id")
        if item_id:
            query = query & (table.item_id == item_id)
        quantity = data.get("quantity")
        if quantity:
            query = query & (table.quantity == quantity)
        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
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

        A Distribution is an Item (which could be a Kit) distributed to a single Location
        - usually as part of an Activity
    """

    names = ("supply_distribution_item",
             "supply_distribution",
             )

    def model(self):

        settings = current.deployment_settings
        if not settings.has_module("stats"):
            # Distribution Model needs Stats module enabling
            return dict()

        T = current.T
        db = current.db
        s3 = current.response.s3

        configure = self.configure
        crud_strings = s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Distribution Item
        #
        tablename = "supply_distribution_item"
        define_table(tablename,
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
            label_create = ADD_ITEM,
            title_display = T("Distribution Item"),
            title_list = T("Distribution Items"),
            title_update = T("Edit Distribution Item"),
            label_list_button = T("List Distribution Items"),
            msg_record_created = T("Distribution Item Added"),
            msg_record_modified = T("Distribution Item Updated"),
            msg_record_deleted = T("Distribution Item Deleted"),
            msg_list_empty = T("No Distribution Items Found")
        )

        # Resource Configuration
        configure(tablename,
                  onaccept = self.supply_distribution_item_onaccept,
                  super_entity = ("stats_parameter", "supply_item_entity"),
                  )

        # ---------------------------------------------------------------------
        # Distribution
        #
        tablename = "supply_distribution"
        define_table(tablename,
                     # Instance
                     super_link("data_id", "stats_data"),
                     # Component (each Distribution can link to a single Project)
                     #self.project_project_id(),
                     # Component (each Distribution can link to a single Activity)
                     self.project_activity_id(),
                     # This is a component, so needs to be a super_link
                     # - can't override field name, ondelete or requires
                     super_link("parameter_id", "stats_parameter",
                                label = T("Item"),
                                instance_types = ("supply_distribution_item",),
                                represent = S3Represent(lookup="stats_parameter"),
                                readable = True,
                                writable = True,
                                empty = False,
                                comment = S3AddResourceLink(c="supply",
                                                            f="distribution_item",
                                                            vars = dict(child = "parameter_id"),
                                                            title=ADD_ITEM),
                                ),
                     self.gis_location_id(),
                     Field("value", "integer",
                           label = T("Quantity"),
                           requires = IS_INT_IN_RANGE(0, 99999999),
                           represent = lambda v: \
                           IS_INT_AMOUNT.represent(v),
                           ),
                     s3_date("date",
                             #empty = False,
                             label = T("Start Date"),
                             ),
                     s3_date("end_date",
                             #empty = False,
                             label = T("End Date"),
                             ),
                     #self.stats_source_id(),
                     Field.Method("year", self.supply_distribution_year),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_DIST = T("Add Distribution")
        crud_strings[tablename] = Storage(
            label_create = ADD_DIST,
            title_display = T("Distribution Details"),
            title_list = T("Distributions"),
            title_update = T("Edit Distribution"),
            title_report = T("Distribution Report"),
            label_list_button = T("List Distributions"),
            msg_record_created = T("Distribution Added"),
            msg_record_modified = T("Distribution Updated"),
            msg_record_deleted = T("Distribution Deleted"),
            msg_list_empty = T("No Distributions Found")
        )

        # Reusable Field
        #represent = S3Represent(lookup=tablename,
        #                        field_sep = " ",
        #                        fields=["value", "parameter_id"])

        # Resource Configuration
        # ---------------------------------------------------------------------
        def year_options():
            """
                returns a dict of the options for the year virtual field
                used by the search widget

                orderby needed for postgres
            """

            table = db.supply_distribution
            query = (table.deleted == False)
            min_field = table.date.min()
            date_min = db(query).select(min_field,
                                        orderby=min_field,
                                        limitby=(0, 1)
                                        ).first()
            start_year = date_min and date_min[min_field].year

            max_field = table.date.max()
            date_max = db(query).select(max_field,
                                        orderby=max_field,
                                        limitby=(0, 1)
                                        ).first()
            last_start_year = date_max and date_max[max_field].year

            max_field = table.end_date.max()
            date_max = db(query).select(max_field,
                                        orderby=max_field,
                                        limitby=(0, 1)
                                        ).first()
            last_end_year = date_max and date_max[max_field].year

            end_year = max(last_start_year, last_end_year)

            if not start_year or not end_year:
                return {start_year:start_year} or {end_year:end_year}
            years = {}
            for year in xrange(start_year, end_year + 1):
                years[year] = year
            return years

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        # Normally only used in Report
        filter_widgets = [
            #S3TextFilter([#"item_id$name",
            #          if settings.get_project_projects():
            #              "activity_id$project_id$name", 
            #              "activity_id$project_id$code",
            #              "location_id",
            #              "comments"
            #              ],
            #             label = T("Search Distributions"),
            #             ),
            S3LocationFilter("location_id",
                             levels=levels,
                             widget="multiselect"
                             ),
            S3OptionsFilter("activity_id$activity_organisation.organisation_id",
                            widget="multiselect"
                            ),
            S3OptionsFilter("parameter_id",
                            label = T("Item"),
                            widget="multiselect"
                            ),
            # @ToDo: Range Slider using start_date & end_date
            #S3DateFilter("date",
            #             )
            # @ToDo: OptionsFilter working with Lazy VF
            #S3OptionsFilter("year",
            #                label=T("Year"),
            #                options = year_options,
            #                widget="multiselect",
            #                hidden=True,
            #                ),
            ]

        list_fields = ["activity_id$activity_organisation.organisation_id",
                       (T("Item"), "parameter_id"),
                       "value",
                       (T("Year"), "year"),
                       ]

        report_fields = ["activity_id$activity_organisation.organisation_id",
                         (T("Item"), "parameter_id"),
                         "parameter_id",
                         (T("Year"), "year"),
                         ]

        if settings.get_project_sectors():
            report_fields.append("activity_id$sector_activity.sector_id")
            filter_widgets.insert(0,
                S3OptionsFilter("activity_id$sector_activity.sector_id",
                                # Doesn't allow translation
                                #represent="%(name)s",
                                widget="multiselect",
                                #hidden=True,
                                ))

        if settings.get_project_hazards():
            report_fields.append("activity_id$project_id$hazard.name")

        if settings.get_project_projects():
            list_fields.insert(0, "activity_id$project_id")
            report_fields.append("activity_id$project_id")
            filter_widgets.append(
                S3OptionsFilter("activity_id$project_id",
                                widget="multiselect"
                                ),
                #S3OptionsFilter("activity_id$project_id$organisation_id",
                #                label = T("Lead Organization"),
                #                widget="multiselect"
                #                ),
                #S3OptionsFilter("activity_id$project_id$partner.organisation_id",
                #                label = T("Partners"),
                #                widget="multiselect"),
                #S3OptionsFilter("activity_id$project_id$donor.organisation_id",
                #                label = T("Donors"),
                #                location_level="L1",
                #                widget="multiselect")
                )

        if settings.get_project_themes():
            report_fields.append("activity_id$project_id$theme.name")
            filter_widgets.append(
                S3OptionsFilter("activity_id$project_id$theme_project.theme_id",
                                # Doesn't allow translation
                                #represent="%(name)s",
                                widget="multiselect",
                                #hidden=True,
                                ))

        for level in levels:
            lfield = "location_id$%s" % level
            list_fields.append(lfield)
            report_fields.append(lfield)

        if "L0" in levels:
            default_row = "location_id$L0"
        elif "L1" in levels:
            default_row = "location_id$L1"
        else:
            default_row = "activity_id$activity_organisation.organisation_id"

        report_options = Storage(rows = report_fields,
                                 cols = report_fields,
                                 fact = [(T("Number of Items"), "sum(value)"),
                                         ],
                                 defaults = Storage(rows = default_row,
                                                    cols = "parameter_id",
                                                    fact = "sum(value)",
                                                    totals = True,
                                                    ),
                                 # Needed for Virtual Field
                                 extra_fields = ["date",
                                                 "end_date",
                                                 ]
                                 )

        configure(tablename,
                  context = {"location": "location_id",
                             "organisation": "activity_id$organisation_activity.organisation_id",
                             },
                  deduplicate = self.supply_distribution_deduplicate,
                  filter_widgets = filter_widgets,
                  onaccept = self.supply_distribution_onaccept,
                  report_options = report_options,
                  super_entity = "stats_data",
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
    def supply_distribution_deduplicate(item):
        """ Import item de-duplication """

        data = item.data
        activity_id = data.get("activity_id")
        location_id = data.get("location_id")
        parameter_id = data.get("parameter_id")

        if activity_id and location_id and parameter_id:
            # Match distribution by activity, item and location
            table = item.table
            query = (table.activity_id == activity_id) & \
                    (table.location_id == location_id) & \
                    (table.parameter_id == parameter_id)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE

    # ---------------------------------------------------------------------
    @staticmethod
    def supply_distribution_onaccept(form):
        """
            Set supply_distribution location, start_date and end_date
            from activity
            This is for when the data is created after the project_activity
            - CSV imports into project_activity
            - Inline forms in project_activity
        """

        db = current.db
        dtable = db.supply_distribution
        record_id = form.vars.id

        # Get the full record
        record = db(dtable.id == record_id).select(dtable.activity_id,
                                                   dtable.location_id,
                                                   dtable.date,
                                                   dtable.end_date,
                                                   limitby=(0, 1)
                                                   ).first()
        try:
            location_id = record.location_id
            start_date = record.date
            end_date = record.end_date
        except:
            # Exit Gracefully
            current.log.warning("Cannot find Distribution: %s" % record_id)
            return

        activity_id = record.activity_id
        if not activity_id:
            # Nothing we can do
            return

        # Read Activity
        atable = db.project_activity
        activity = db(atable.id == activity_id).select(atable.location_id,
                                                       atable.date,
                                                       atable.end_date,
                                                       limitby=(0, 1)
                                                       ).first()
        try:
            a_location_id = activity.location_id
            a_start_date = activity.date
            a_end_date = activity.end_date
        except:
            # Exit Gracefully
            current.log.warning("Cannot find Activity: %s" % activity_id)
            return

        data = {}
        if a_location_id and a_location_id != location_id:
            data["location_id"] = a_location_id
        if a_start_date and a_start_date != start_date:
            data["date"] = a_start_date
        if a_end_date and a_end_date != end_date:
            data["end_date"] = a_end_date

        if data:
            # Update Distribution details
            db(dtable.id == record_id).update(**data)

    # ---------------------------------------------------------------------
    @staticmethod
    def supply_distribution_year(row):
        """ Virtual field for the supply_distribution table """

        if hasattr(row, "supply_distribution"):
            row = row.supply_distribution

        try:
            date = row.date
        except AttributeError:
            date = None
        try:
            end_date = row.end_date
        except AttributeError:
            end_date = None

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
                sep = "-"
            else:
                sep = " - "
            name = "%s%s%s" % (name, sep, parent)
            grandparent = row["supply_grandparent_item_category.name"]
            if grandparent:
                name = "%s%s%s" % (name, sep, grandparent)
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
                        name = "%s%s%s" % (name, sep, greatgrandparent)
                        if greatgreatgrandparent:
                            name = "%s%s%s" % (name, sep, greatgreatgrandparent)
                            if use_code:
                                greatgreatgreatgrandparent = row["supply_grandparent_item_category.code"]
                            else:
                                greatgreatgreatgrandparent = row["supply_grandparent_item_category.name"] or row["supply_grandparent_item_category.code"]
                            if greatgreatgreatgrandparent:
                                name = "%s%s%s" % (name, sep, greatgreatgreatgrandparent)

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
                                                   filter_opts = (r.record.id,),
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

        elif r.representation == "xls":
            # Use full Category names in XLS output
            s3db.supply_item.item_category_id.represent = \
                supply_ItemCategoryRepresent(use_code=False)

        return True
    s3.prep = prep

    return current.rest_controller("supply", "item",
                                   rheader = supply_item_rheader,
                                   )

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
        label_create = T("Add Item"),
        title_display = T("Item Details"),
        title_list = T("Items"),
        title_update = T("Edit Item"),
        label_list_button = T("List Items"),
        label_delete_button = T("Delete Item"),
        msg_record_created = T("Item added"),
        msg_record_modified = T("Item updated"),
        msg_record_deleted = T("Item deleted"),
        msg_list_empty = T("No Items currently registered"))

    table.category = Field.Method("category",
                                  supply_item_entity_category)
    table.country = Field.Method("country",
                                 supply_item_entity_country)
    table.organisation = Field.Method("organisation",
                                      supply_item_entity_organisation)
    table.contacts = Field.Method("contacts",
                                  supply_item_entity_contacts)
    table.status = Field.Method("status",
                                supply_item_entity_status)

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
                inv_itable = s3db.inv_inv_item
                iquery = query & (inv_itable.site_id == table.site_id)
                isites = db(iquery).select(distinct=True, *fields)
                inv_ttable = s3db.inv_track_item
                inv_rtable = s3db.inv_recv
                rquery = query & (inv_ttable.send_inv_item_id == inv_rtable.id) & \
                                 (inv_rtable.site_id == table.site_id)
                rsites = db(rquery).select(distinct=True, *fields)
            if settings.has_module("proc"):
                proc_ptable = s3db.proc_plan
                proc_itable = s3db.proc_plan_item
                pquery = query & (proc_itable.plan_id == proc_ptable.id) & \
                                 (proc_ptable.site_id == table.site_id)
                psites = db(pquery).select(distinct=True, *fields)
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

    output = current.rest_controller("supply", "item_entity",
                                     hide_filter = True,
                                    )
    return output

# -------------------------------------------------------------------------
def supply_get_shipping_code(type, site_id, field):

    db = current.db
    if site_id:
        table = current.s3db.org_site
        site = db(table.site_id == site_id).select(table.code,
                                                   limitby=(0, 1)
                                                   ).first()
        if site:
            scode = site.code
        else:
            scode = "###"
        code = "%s-%s-" % (type, scode)
    else:
        code = "%s-###-" % (type)
    number = 0
    if field:
        query = (field.like("%s%%" % code))
        ref_row = db(query).select(field,
                                   limitby=(0, 1),
                                   orderby=~field).first()
        if ref_row:
            ref = ref_row(field)
            number = int(ref[-6:])

    return "%s%06d" % (code, number+1)

# END =========================================================================
