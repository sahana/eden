# -*- coding: utf-8 -*-

""" Sahana Eden Climate Model

    @copyright: 2011-2012 (c) Sahana Software Foundation
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

__all__ = ["S3ClimateModel",
           "climate_first_run",
           ]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3ClimateModel(S3Model):
    """
        Climate data is stored in dynamically created tables.
        These tables can be added from the command line script add_table.py
        in modules.ClimateDataPortal.
        The table definitions are stored in climate_sample_table_spec.

        A data is an observed value over a time quantum at a given place.

        e.g. observed temperature in Kathmandu between Feb 2006 - April 2007

        Places are currently points, i.e. lat/lon coordinates.
        Places may be stations.
        Places may have elevation or other optional information.

        @ToDo: i18n
        @ToDo: Deprecate raw SQL (Tested only on PostgreSQL)
    """

    names = ["climate_place",
             "climate_place_elevation",
             "climate_place_station_name",
             "climate_place_station_id",
             "climate_sample_table_spec",
             "climate_monthly_aggregation",
             "climate_station_parameter",
             "climate_prices",
             "climate_purchase",
             "climate_save_query",
             ]

    def model(self):

        T = current.T
        auth = current.auth
        db = current.db
        s3 = current.response.s3
        utcnow = current.request.utcnow

        NONE = current.messages.NONE

        configure = self.configure
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Climate Place
        #
        # This resource is spread over 4 tables, which we assume are linked by
        # common IDs
        #
        # @ToDo: Migrate to gis_location?
        # Although this table has many fields unused so a performance hit?
        # elevation is not included as it would just mean a performance hit
        # when we are generating 2D maps without elevation info.
        define_table("climate_place",
                     Field("longitude", "double",
                           notnull=True,
                           required=True,
                          ),
                     Field("latitude", "double",
                           notnull=True,
                           required=True,
                          )
                    )

        # ---------------------------------------------------------------------
        # elevation may not be useful for future projects
        # e.g. where not available, or sea-based stations
        # also, elevation may be supplied for gridded data
        define_table("climate_place_elevation",
                     Field("elevation_metres", "double",
                           notnull=True,
                           required=True,
                          ),
                    )

        # ---------------------------------------------------------------------
        # not all places are stations with elevations
        # as in the case of "gridded" data
        # a station can only be in one place
        table = define_table("climate_place_station_name",
                             Field("name", "double",
                                   notnull=True,
                                   required=True,
                                  ),
                            )

        station_id = S3ReusableField("station_id", table,
                                     sortby="name",
                                     requires = IS_ONE_OF(db,
                                        "climate_place_station_name.id",
                                        climate_station_represent,
                                        orderby="climate_place_station_name.name",
                                        sort=True
                                        ),
                                     represent = climate_station_represent,
                                     label = "Station",
                                     ondelete = "RESTRICT"
                                    )

        # ---------------------------------------------------------------------
        # station id may not be useful or even meaningful
        # e.g. gridded data has no stations.
        # this is passive data so ok to store separately
        define_table("climate_place_station_id",
                     Field("station_id", "integer",
                           notnull=True,
                           required=True,
                          ),
                    )

        # ---------------------------------------------------------------------
        # coefficient of variance is meaningless for degrees C but Ok for Kelvin
        # internally all scales must be ratio scales if coefficient
        # of variations is to be allowed, (which it is)
        # rainfall (mm), temp (K) are ok
        # output units

        table = define_table("climate_sample_table_spec",
                             Field("name",
                                   notnull=True,
                                   required=True,
                                  ),
                             Field("sample_type_code",
                                   length = 1,
                                   notnull = True,
                                   # web2py requires a default value for not null fields
                                   default = "",
                                   required = True
                                  ),
                             Field("field_type",
                                   notnull=True,
                                   required=True,
                                  ),
                             Field("units",
                                   notnull=True,
                                   required=True,
                                  ),
                             Field("date_mapping",
                                   default="",
                                   notnull=True,
                                   required=True
                                  ),
                             Field("grid_size", "double",
                                   default = 0,
                                   notnull = True,
                                   required = True
                                  )
                            )

        parameter_id = S3ReusableField("parameter_id", table,
                                       sortby="name",
                                       requires = IS_ONE_OF(db,
                                                "climate_sample_table_spec.id",
                                                sample_table_spec_represent,
                                                sort=True
                                                ),
                                        represent = sample_table_spec_represent,
                                        label = "Parameter",
                                        ondelete = "RESTRICT"
                                        )

        # ---------------------------------------------------------------------
        define_table("climate_monthly_aggregation",
                     Field("sample_table_id",
                           db.climate_sample_table_spec,
                           notnull = True,
                           required = True
                           ),
                     # this maps to the name of a python class
                     # that deals with the monthly aggregated data.
                     Field("aggregation",
                           notnull=True,
                           required=True,
                          )
                    )

        # ---------------------------------------------------------------------
        # Station Parameters
        #
        tablename = "climate_station_parameter"
        table = define_table(tablename,
                             station_id(),
                             parameter_id(
                                requires = IS_ONE_OF(db,
                                    "climate_sample_table_spec.id",
                                    sample_table_spec_represent,
                                    sort=True
                                ),
                             ),
                            )

        CRUD_strings(tablename,
                     entity = "Station Parameter")

        table.virtualfields.append(station_parameters_virtualfields())

        configure(tablename,
                  insertable = False,
                  list_fields = [
                            "station_id",
                            "parameter_id",
                            (T("Range From"), "range_from"),
                            (T("Range To"), "range_to"),
                        ]
                  )

        # =====================================================================
        # Purchase Data
        #
        nationality_opts = {
            1:"Nepali Student",
            2:"Others"
        }

        tablename = "climate_prices"
        define_table(tablename,
                     Field("category", "integer",
                           label = T("Category"),
                           requires = IS_IN_SET(nationality_opts),
                           represent = lambda id: nationality_opts.get(id, NONE),
                           notnull = True,
                           required = True
                     ),
                     parameter_id(
                        requires = IS_ONE_OF(db,
                            "climate_sample_table_spec.id",
                            sample_table_spec_represent,
                            filterby = "sample_type_code",
                            filter_opts = ["O"],
                            sort=True
                        ),
                        notnull = True,
                        required = True,
                        represent = sample_table_spec_represent
                     ),
                     Field("nrs_per_datum", "double",
                           label = T("NRs per datum"),
                           notnull = True,
                           required = True
                          )
                    )

        configure(tablename,
                  create_onvalidation = self.climate_price_create_onvalidation,
                  list_fields=[
                        "category",
                        "parameter_id",
                        "nrs_per_datum"
                    ]
                )

        CRUD_strings(tablename,
                     entity = "Dataset Price")

        tablename = "climate_purchase"
        table = define_table(tablename,
                             #user_id(),
                             #Field("sample_type_code",
                             #      "string",
                             #      requires = IS_IN_SET(sample_type_code_opts),
                             #      represent = lambda code: ClimateDataPortal.sample_table_types_by_code[code]
                             #),
                             Field("parameter_id", "integer",
                                   requires = IS_ONE_OF(db,
                                            "climate_prices.parameter_id",
                                            sample_table_spec_represent,
                                            ),
                                   represent = sample_table_spec_represent,
                                   label = "Parameter",
                                   ondelete = "RESTRICT"
                                ),
                             station_id(),
                             s3_date("date_from",
                                     default = "now",
                                     empty=False
                                    ),
                             s3_date("date_to",
                                     default = "now",
                                     empty=False
                                    ),
                             Field("nationality", "integer",
                                   label = T("Category"),
                                   requires = IS_IN_SET(nationality_opts),
                                   represent = lambda id: nationality_opts.get(id, NONE),
                                   required = True
                                   ),
                             Field("notes", "text",
                                   label = T("Receipt number / Student ID / other notes")
                                   ),
                             Field("price"),
                             Field("paid", "boolean",
                                   represent = lambda opt: \
                                        opt and "Yes" or "No",
                                  ),
                             Field("i_agree_to_the_terms_and_conditions", "boolean",
                                   required = True,
                                   represent = lambda agrees: agrees and "Yes" or "No",
                                   comment = DIV(_class="stickytip",
                                                 _title="%s|%s" % (
                                        T("Important"),
                                        T("Check this box when you have read, "
                                          "understand and agree to the "
                                          "<a href='terms' target='_blank'>"
                                          "terms and conditions"
                                          "</a>."
                                         )
                                        )
                                       )
                                   ),
                             *s3_meta_fields()
                            )
        table.owned_by_user.label = T("User")

        system_roles = auth.get_system_roles()
        ADMIN = system_roles.ADMIN
        if not auth.s3_has_role(ADMIN):
            table.paid.writable = False

        CRUD_strings(tablename,
                     entity = "Purchased Data Detail",
                     CREATE = T("Purchase New Data"),
                     created = T("Data Purchase In Process"),
                     LIST = T("All Purchased Data")
                    )

        configure(tablename,
                  onaccept = self.climate_purchase_onaccept,
                  create_next = URL(args = ["[id]", "read"]),
                  list_fields=[
                        "owned_by_user",
                        "parameter_id",
                        "station_id",
                        "date_from",
                        "date_to",
                        "nationality",
                        #"purpose",
                        "price",
                        "paid",
                        "i_agree_to_terms_and_conditions"
                    ]
                )

        # =====================================================================
        # Saved Queries
        #
        tablename = "climate_save_query"
        define_table(tablename,
                     #user_id(),
                     Field("description"),
                     Field("query_definition", "text"),
                     )

        CRUD_strings(tablename,
                     entity = "Saved Query",
                     CREATE = T("Save Query"),
                     created = "Query Saved",
                     LIST = T("Saved Queries")
                    )

        configure(tablename,
                  listadd = False)

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def climate_price_create_onvalidation(form):
        """
        """

        vars = form.request_vars
        db = current.db
        table = db.climate_prices
        query = (table.category == vars["category"]) & \
                (table.parameter_id == vars["parameter_id"])
        price = db(query).select(table.id,
                                         limitby=(0, 1)).first()
        if price is not None:
            form.errors["nrs_per_datum"] = [
                "There is a conflicting price for the above category and parameter."
            ]
            return False
        else:
            return True

    # -------------------------------------------------------------------------
    @staticmethod
    def climate_purchase_onaccept(form):
        """
            Calculate Price
        """

        import ClimateDataPortal

        vars = form.vars
        id = vars.id

        db = current.db
        ptable = db.climate_purchase
        purchase = db(ptable.id == id).select(ptable.paid,
                                              limitby=(0, 1)).first()

        if (purchase and purchase.paid == True):
            pass
        else:
            parameter_id = vars.parameter_id
            table = db.climate_sample_table_spec
            query = (table.id == parameter_id)
            parameter_table = db(query).select(table.id,
                                               table.date_mapping,
                                               limitby=(0, 1)).first()
            parameter_table_id = parameter_table.id
            date_mapping_name = parameter_table.date_mapping
            period = date_mapping_name

            date_from = vars.date_from
            date_to = vars.date_to
            nationality = int(vars.nationality)
            table = db.climate_prices
            query = (table.category == nationality) & \
                    (table.parameter_id == parameter_id)
            price_row = db(query).select(table.nrs_per_datum,
                                         limitby=(0, 1)).first()

            if price_row is None:
                form.errors["price"] = ["There is no price set for this data"]
            else:
                price = price_row.nrs_per_datum

                currency = {
                    1: "%.2f NRs",
                    2: "US$ %.2f"
                }[nationality]

                date_mapping = getattr(ClimateDataPortal, date_mapping_name)

                start_date_number = date_mapping.date_to_time_period(date_from)
                end_date_number = date_mapping.date_to_time_period(date_to)

                place_id = int(vars.station_id)

                datum_count = db.executesql(
                    "SELECT COUNT(*) "
                    "FROM climate_sample_table_%(parameter_table_id)i "
                    "WHERE place_id = %(place_id)i "
                    "AND time_period >= %(start_date_number)i "
                    "AND time_period <= %(end_date_number)i;" % locals()
                )[0][0]
                ptable[id] = {"price": currency % (datum_count * price)}

# =============================================================================
def climate_station_represent(id):
    """
    """

    s3db = current.s3db
    table = s3db.climate_place_station_id
    row_id = db(table.id == id).select(table.station_id,
                                       limitby=(0,1)).first()
    table = s3db.climate_place_station_name
    row_name = db(table.id == id).select(table.name,
                                         limitby=(0,1)).first()

    if row_id and row_id.station_id:
        represent = " (%s)" % row_id.station_id
    else:
        represent = ""
    if row_name and row_name.name:
        represent = "%s%s" % (row_name.name, represent)

    return represent or current.messages.NONE

# =============================================================================
def sample_table_spec_represent(id):
    """
    """

    import ClimateDataPortal

    table = current.s3db.climate_sample_table_spec
    row = current.db(table.id == id).select(table.name,
                                            table.sample_type_code,
                                            limitby=(0, 1)).first()
    if row:
        return "%s %s" % (
            ClimateDataPortal.sample_table_types_by_code[row.sample_type_code].__name__,
            row.name
        )
    else:
        return current.messages.NONE

# =============================================================================
class station_parameters_virtualfields(dict, object):

    # -------------------------------------------------------------------------
    def range_from(self):
        try:
            query = (
                "SELECT MIN(time_period) "
                "from climate_sample_table_%(parameter_id)i "
                "WHERE place_id = %(station_id)i;"
            ) % dict(
                parameter_id = self.climate_station_parameter.parameter_id,
                station_id = self.climate_station_parameter.station_id,
            )
        except AttributeError:
            return current.messages.NONE
        date  = current.db.executesql(query)[0][0]
        if date is not None:
            import ClimateDataPortal
            year, month = ClimateDataPortal.month_number_to_year_month(date)
            return "%s-%s" % (month, year)
        else:
            return current.messages.NONE

    # -------------------------------------------------------------------------
    def range_to(self):
        try:
            query = (
                "SELECT MAX(time_period) "
                "from climate_sample_table_%(parameter_id)i "
                "WHERE place_id = %(station_id)i;"
            ) % dict(
                parameter_id = self.climate_station_parameter.parameter_id,
                station_id = self.climate_station_parameter.station_id,
            )
        except AttributeError:
            return current.messages.NONE
        date  = current.db.executesql(query)[0][0]
        if date is not None:
            import ClimateDataPortal
            year, month = ClimateDataPortal.month_number_to_year_month(date)
            return "%s-%s" % (month, year)
        else:
            return current.messages.NONE

# =============================================================================
def CRUD_strings(tablename,
                 entity,
                 entities = None,
                 CREATE = None,
                 created = None,
                 LIST = None
                ):
    """
        Non-i18n way of creating CRUD Strings

        @ToDo: Deprecate
    """

    T = current.T

    if entities is None:
        entities = entity+"s"
    if CREATE is None:
        CREATE = T("Add new "+entity)
    if created is None:
        created = entity+" added"
    if LIST is None:
        LIST = T("List "+entities)
    current.response.s3.crud_strings[tablename] = Storage(
        title_create = CREATE,
        title_display = T(entity+" Details"),
        title_list = T(entities),
        title_update = T("Edit "+entity),
        title_search = T("Search "+entities),
        subtitle_create = CREATE,
        label_list_button = LIST,
        label_create_button = CREATE,
        label_delete_button = T("Remove "+entity),
        msg_record_created = T(created),
        msg_record_modified = T(entity+" updated"),
        msg_record_deleted = T(entity+" removed"),
        msg_list_empty = T("No "+entities))

# =============================================================================
def climate_first_run():
    """
        Called from zzz_1st_run.py
        Manual SQL Statements to run after tables are created
    """

    db = current.db
    # Load all stations and parameters
    s3db = current.s3db
    ptable = s3db.climate_station_parameter
    if not db(ptable.id > 0).select(ptable.id,
                                    limitby=(0, 1)):
        table = s3db.climate_place_station_name
        station_rows = db(table.id > 0).select(table.id)
        table = db.climate_sample_table_spec
        query = (table.sample_type_code == "O")
        for station_row in station_rows:
            parameter_rows = db(query).select(table.id)
            for parameter_row in parameter_rows:
                ptable.insert(
                    station_id = station_row.id,
                    parameter_id = parameter_row.id
                )

    db.executesql(
        "ALTER TABLE climate_sample_table_spec"
        "ADD CONSTRAINT climate_sample_table_name_sample_type_unique"
        "UNIQUE (name, sample_type_code);"
        "ALTER TABLE climate_prices"
        "ADD CONSTRAINT climate_price_unique"
        "UNIQUE (category, parameter_id);"
    )
    db.commit()

# END =========================================================================
