# -*- coding: utf-8 -*-

"""
    Supply

    Generic Supply functionality such as catalogs and items that will be used across multiple modules
"""

# -----------------------------------------------------------------------------
# Defined in the Model for use from Multiple Controllers for unified menus
#
def supply_item_controller():
    """ RESTful CRUD controller """

    if "vehicle" in request.get_vars:
        # Limit the Categories to just those with vehicles in
        field = s3db.supply_item.item_category_id
        field.requires = IS_NULL_OR(IS_ONE_OF(db,
                                              "supply_item_category.id",
                                              "%(name)s",
                                              sort=True,
                                              filterby = "is_vehicle",
                                              filter_opts = [True])
                                            )

    s3mgr.configure("inv_inv_item",
                    listadd=False,
                    deletable=False)

    return s3_rest_controller("supply", "item",
                              rheader=s3db.supply_item_rheader)

# ---------------------------------------------------------------------
def item_entity_controller():
    """
        RESTful CRUD controller
        - consolidated report of inv_item, recv_item & proc_plan_item
        @ToDo: Migrate JS to Static as part of migrating this to an
               S3Search Widget
    """

    tablename = "supply_item_entity"
    table = s3db[tablename]

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
        msg_list_empty = T("No Items currently registered"),
        name_nice = T("Item"),
        name_nice_plural = T("Items"))

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
            table = s3db.supply_item
            try:
                query = (table.id == self.supply_item_entity.item_id)
            except:
                     # We are being instantiated inside one of the other methods
                    return None
            record = db(query).select(table.item_category_id,
                                      limitby=(0, 1)).first()
            if record:
                category = table.item_category_id.represent(record.item_category_id)
            return category

        def country(self):
            country = NONE
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
                record = db(query).select(otable.L0,
                                          limitby=(0, 1)).first()
                if record:
                    country = record.L0 or T("Unknown")
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
                record = db(query).select(otable.L0,
                                          limitby=(0, 1)).first()
                if record:
                    country = record.L0 or T("Unknown")
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
                record = db(query).select(otable.organisation_id,
                                          limitby=(0, 1)).first()
                if record:
                    organisation = organisation_represent(record.organisation_id,
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
                record = db(query).select(otable.organisation_id,
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
                record = db(query).select(itable.site_id,
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
                return NONE

            #site = s3db.org_site_represent(record.site_id)
            #return site
            otable = s3db.org_office
            query = (otable.site_id == record.site_id)
            record = db(query).select(otable.id,
                                      otable.comments,
                                      limitby=(0, 1)).first()
            if request.extension == "xls" or \
               request.extension == "pdf":
                if record.comments:
                    return record.comments
                else:
                    return NONE
            elif record.comments:
                comments = s3_comments_represent(record.comments,
                                                 showlink=False)
            else:
                comments = NONE
            return A(comments,
                     _href = URL(f="office",
                                 args = [record.id]))

        def status(self):
            status = NONE
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
                record = db(query).select(itable.expiry_date,
                                          limitby=(0, 1)).first()
                if record:
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
                record = db(query).select(rtable.eta,
                                          limitby=(0, 1)).first()
                if record:
                    if record.eta:
                        status = T("Planned %(date)s") % dict(date=record.eta)
                    else:
                       status = T("Planned Procurement")
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

# END =========================================================================

