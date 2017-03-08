# -*- coding: utf-8 -*-

""" Sahana Eden Social Tenure Domain Model
    http://stdm.gltn.net/

    @copyright: 2017 (c) Sahana Software Foundation
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

__all__ = ("S3SocialTenureDomainModel",
           "S3InformalSettlementModel",
           "S3LocalGovernmentModel",
           "S3RuralAgricultureModel",
           "stdm_rheader",
           )

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class S3SocialTenureDomainModel(S3Model):

    """ Core STDM Model """

    names = ("stdm_profile",
             "stdm_spatial_unit",
             "stdm_tenure_type",
             "stdm_tenure",
             "stdm_tenure_relationship",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        has_role = current.auth.s3_has_role
        if has_role("ADMIN"):
            spatial_label = T("Spatial Unit")
            spatial_types = Storage(stdm_garden = T("Garden"),
                                    stdm_parcel = T("Parcel"),
                                    stdm_structure = T("Structure"),
                                    )

        elif has_role("INFORMAL_SETTLEMENT"):
            spatial_label = T("Structure")
            spatial_types = Storage(stdm_structure = T("Structure"),
                                    )

        elif has_role("RURAL_AGRICULTURE"):
            spatial_label = T("Garden")
            spatial_types = Storage(stdm_garden = T("Garden"),
                                    )

        elif has_role("LOCAL_GOVERNMENT"):
            spatial_label = T("Parcel")
            spatial_types = Storage(stdm_parcel = T("Parcel"),
                                    )

        else:
            # Unauthenticated scripts
            spatial_label = T("Spatial Unit")
            spatial_types = Storage(stdm_garden = T("Garden"),
                                    stdm_parcel = T("Parcel"),
                                    stdm_structure = T("Structure"),
                                    )

        # ---------------------------------------------------------------------
        # Profiles
        #
        tablename = "stdm_profile"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_PROFILE = T("Create Profile")
        crud_strings[tablename] = Storage(
            label_create = ADD_PROFILE,
            title_display = T("Profile"),
            title_list = T("Profiles"),
            title_update = T("Edit Profile"),
            label_list_button = T("List Profiles"),
            label_delete_button = T("Delete Profile"),
            msg_record_created = T("Profile added"),
            msg_record_modified = T("Profile updated"),
            msg_record_deleted = T("Profile deleted"),
            msg_list_empty = T("No Profiles currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        profile_id = S3ReusableField("profile_id", "reference %s" % tablename,
                                     requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "stdm_profile.id",
                                                          represent,
                                                          sort = True,
                                                          )),
                                     represent=represent,
                                     label=T("Profile"),
                                     ondelete="RESTRICT",
                                     comment = S3PopupLink(c = "stdm",
                                                           f = "profile",
                                                           label = ADD_PROFILE,
                                                           ),
                                     )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Super entity: stdm_spatial_unit
        #
        tablename = "stdm_spatial_unit"
        self.super_entity(tablename, "spatial_unit_id",
                          spatial_types,
                          Field("name",
                                label = T("Name"),
                                ),
                          self.gis_location_id(),
                          #on_define = lambda table: \
                          #   [table.instance_type.set_attributes(readable = True),
                          #    ],
                          )

        # ---------------------------------------------------------------------
        # Tenure Types
        #
        tablename = "stdm_tenure_type"
        define_table(tablename,
                     profile_id(),
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_TYPE = T("Create Tenure Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_TYPE,
            title_display = T("Tenure Type"),
            title_list = T("Tenure Types"),
            title_update = T("Edit Tenure Type"),
            label_list_button = T("List Tenure Types"),
            label_delete_button = T("Delete Tenure Type"),
            msg_record_created = T("Tenure Type added"),
            msg_record_modified = T("Tenure Type updated"),
            msg_record_deleted = T("Tenure Type deleted"),
            msg_list_empty = T("No Tenure Types currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        tenure_type_id = S3ReusableField("tenure_type_id", "reference %s" % tablename,
                                         requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "stdm_tenure_type.id",
                                                              represent,
                                                              sort=True,
                                                              # Done in prep
                                                              #filterby = "profile_id",
                                                              #filter_opts = filter_opts,
                                                              )),
                                         represent=represent,
                                         label=T("Tenure Type"),
                                         ondelete="RESTRICT",
                                         comment = S3PopupLink(c = "stdm",
                                                               f = "tenure_type",
                                                               label = ADD_TYPE,
                                                               ),
                                         )

        configure(tablename,
                  deduplicate = S3Duplicate(primary=("name", "profile_id")),
                  )

        # ---------------------------------------------------------------------
        # Tenures
        #
        tablename = "stdm_tenure"
        define_table(tablename,
                     # Instance
                     super_link("doc_id", "doc_entity"),
                     # Foreign Key
                     super_link("spatial_unit_id", "stdm_spatial_unit",
                                instance_types = spatial_types,
                                label = spatial_label,
                                readable = True,
                                represent = S3Represent("stdm_spatial_unit"),
                                updateable = True,
                                writable = True,
                                ),
                     #s3_date(),
                     #s3_date("end_date"),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Tenure"),
            title_display = T("Tenure"),
            title_list = T("Tenures"),
            title_update = T("Edit Tenure"),
            label_list_button = T("List Tenures"),
            label_delete_button = T("Delete Tenure"),
            msg_record_created = T("Tenure added"),
            msg_record_modified = T("Tenure updated"),
            msg_record_deleted = T("Tenure deleted"),
            msg_list_empty = T("No Tenures currently registered"))

        represent = S3Represent(lookup=tablename, fields=["location_id", "tenure_type_id"])
        tenure_id = S3ReusableField("tenure_id", "reference %s" % tablename,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "srdm_tenure.id",
                                                          represent,
                                                          sort=True)),
                                    represent=represent,
                                    label=T("Tenure"),
                                    ondelete="RESTRICT",
                                    )

        crud_form = S3SQLCustomForm("spatial_unit_id",
                                    S3SQLInlineComponent("tenure_relationship",
                                                         fields=["pe_id",
                                                                 "tenure_type_id",
                                                                 ],
                                                         ),
                                    "comments",
                                    )

        configure(tablename,
                  crud_form = crud_form,
                  super_entity = "doc_entity",
                  )

        self.add_components(tablename,
                            stdm_tenure_relationship = "tenure_id",
                            )

        # ---------------------------------------------------------------------
        # Tenures <> Person Entities link
        #
        tablename = "stdm_tenure_relationship"
        define_table(tablename,
                     tenure_id(),
                     super_link("pe_id", "pr_pentity",
                                label = T("Party"),
                                readable = True,
                                writable = True,
                                represent = self.pr_PersonEntityRepresent(show_label=False),
                                sort = True,
                                empty = False,
                                ),
                     tenure_type_id(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        #crud_strings[tablename] = Storage(
        #    label_create = T("Create Tenure Relationship"),
        #    title_display = T("Tenure Relationship"),
        #    title_list = T("Tenure Relationships"),
        #    title_update = T("Edit Tenure Relationship"),
        #    label_list_button = T("List Tenure Relationships"),
        #    label_delete_button = T("Delete Tenure Relationship"),
        #    msg_record_created = T("Tenure Relationship added"),
        #    msg_record_modified = T("Tenure Relationship updated"),
        #    msg_record_deleted = T("Tenure Relationship deleted"),
        #    msg_list_empty = T("No Tenure Relationships currently registered"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3InformalSettlementModel(S3Model):

    """ Informal Settlement Profile """

    names = ("stdm_ownership_type",
             "stdm_structure",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Ownership Types
        #
        tablename = "stdm_ownership_type"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_TYPE = T("Create Ownership Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_TYPE,
            title_display = T("Ownership Type"),
            title_list = T("Ownership Types"),
            title_update = T("Edit Ownership Type"),
            label_list_button = T("List Ownership Types"),
            label_delete_button = T("Delete Ownership Type"),
            msg_record_created = T("Ownership Type added"),
            msg_record_modified = T("Ownership Type updated"),
            msg_record_deleted = T("Ownership Type deleted"),
            msg_list_empty = T("No Ownership Types currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        ownership_type_id = S3ReusableField("ownership_type_id", "reference %s" % tablename,
                                            requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "stdm_ownership_type.id",
                                                                  represent,
                                                                  sort=True)),
                                            represent=represent,
                                            label=T("Ownership Type"),
                                            ondelete="RESTRICT",
                                            comment = S3PopupLink(c = "stdm",
                                                                  f = "ownership_type",
                                                                  label = ADD_TYPE,
                                                                  ),
                                            )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Structures
        #
        tablename = "stdm_structure"
        define_table(tablename,
                     # Instance
                     self.super_link("spatial_unit_id", "stdm_spatial_unit"),
                     Field("name2",
                           label = T("Name"),
                           ),
                     Field("name",
                           label = T("Code"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     self.gis_location_id(
                         widget = S3LocationSelector(catalog_layers = True,
                                                     points = True,
                                                     polygons = True,
                                                     ),
                     ),
                     ownership_type_id(),
                     Field("recognition_status", "boolean",
                           label = T("Recognition Status"),
                           represent = s3_yes_no_represent,
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Structure"),
            title_display = T("Structure"),
            title_list = T("Structures"),
            title_update = T("Edit Structure"),
            label_list_button = T("List Structures"),
            label_delete_button = T("Delete Structure"),
            msg_record_created = T("Structure added"),
            msg_record_modified = T("Structure updated"),
            msg_record_deleted = T("Structure deleted"),
            msg_list_empty = T("No Structures currently registered"))

        configure(tablename,
                  super_entity = "stdm_spatial_unit",
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3LocalGovernmentModel(S3Model):

    """ Local Government Profile """

    names = ("stdm_parcel_type",
             "stdm_landuse",
             "stdm_dispute",
             "stdm_parcel",
             "stdm_job_title",
             "stdm_surveyor",
             "stdm_planner",
             "stdm_gov_survey",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        person_id = self.pr_person_id

        # ---------------------------------------------------------------------
        # Parcel Types
        #
        tablename = "stdm_parcel_type"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_TYPE = T("Create Parcel Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_TYPE,
            title_display = T("Parcel Type"),
            title_list = T("Parcel Types"),
            title_update = T("Edit Parcel Type"),
            label_list_button = T("List Parcel Types"),
            label_delete_button = T("Delete Parcel Type"),
            msg_record_created = T("Parcel Type added"),
            msg_record_modified = T("Parcel Type updated"),
            msg_record_deleted = T("Parcel Type deleted"),
            msg_list_empty = T("No Parcel Types currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        parcel_type_id = S3ReusableField("parcel_type_id", "reference %s" % tablename,
                                         requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "stdm_parcel_type.id",
                                                              represent,
                                                              sort=True)),
                                         represent=represent,
                                         label=T("Parcel Type"),
                                         ondelete="RESTRICT",
                                         comment = S3PopupLink(c = "stdm",
                                                               f = "parcel_type",
                                                               label = ADD_TYPE,
                                                               ),
                                         )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Land Uses
        #
        tablename = "stdm_landuse"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_TYPE = T("Create Land Use")
        crud_strings[tablename] = Storage(
            label_create = ADD_TYPE,
            title_display = T("Land Use"),
            title_list = T("Land Uses"),
            title_update = T("Edit Land Use"),
            label_list_button = T("List Land Uses"),
            label_delete_button = T("Delete Land Use"),
            msg_record_created = T("Land Use added"),
            msg_record_modified = T("Land Use updated"),
            msg_record_deleted = T("Land Use deleted"),
            msg_list_empty = T("No Land Uses currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        landuse_id = S3ReusableField("landuse_id", "reference %s" % tablename,
                                     requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "stdm_landuse.id",
                                                          represent,
                                                          sort=True)),
                                     represent=represent,
                                     label=T("Land Use"),
                                     ondelete="RESTRICT",
                                     comment = S3PopupLink(c = "stdm",
                                                           f = "landuse",
                                                           label = ADD_TYPE,
                                                           ),
                                     )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Disputes
        #
        tablename = "stdm_dispute"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_TYPE = T("Create Dispute")
        crud_strings[tablename] = Storage(
            label_create = ADD_TYPE,
            title_display = T("Dispute"),
            title_list = T("Disputes"),
            title_update = T("Edit Dispute"),
            label_list_button = T("List Disputes"),
            label_delete_button = T("Delete Dispute"),
            msg_record_created = T("Dispute added"),
            msg_record_modified = T("Dispute updated"),
            msg_record_deleted = T("Dispute deleted"),
            msg_list_empty = T("No Disputes currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        dispute_id = S3ReusableField("dispute_id", "reference %s" % tablename,
                                     requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "stdm_dispute.id",
                                                          represent,
                                                          sort=True)),
                                     represent=represent,
                                     label=T("Dispute"),
                                     ondelete="RESTRICT",
                                     comment = S3PopupLink(c = "stdm",
                                                           f = "dispute",
                                                           label = ADD_TYPE,
                                                           ),
                                     )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Parcels
        #
        tablename = "stdm_parcel"
        define_table(tablename,
                     # Instance
                     super_link("spatial_unit_id", "stdm_spatial_unit"),
                     Field("name",
                           label = T("Code"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("area", "integer",
                           label = T("Area"),
                           # Units?
                           ),
                     s3_currency(),
                     Field("value", "integer",
                           label = T("Value"),
                           ),
                     parcel_type_id(),
                     landuse_id(),
                     dispute_id(),
                     self.gis_location_id(
                         widget = S3LocationSelector(catalog_layers = True,
                                                     points = True,
                                                     polygons = True,
                                                     ),
                     ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Parcel"),
            title_display = T("Parcel"),
            title_list = T("Parcels"),
            title_update = T("Edit Parcel"),
            label_list_button = T("List Parcels"),
            label_delete_button = T("Delete Parcel"),
            msg_record_created = T("Parcel added"),
            msg_record_modified = T("Parcel updated"),
            msg_record_deleted = T("Parcel deleted"),
            msg_list_empty = T("No Parcels currently registered"))

        configure(tablename,
                  super_entity = "stdm_spatial_unit",
                  )

        # ---------------------------------------------------------------------
        # Job Titles
        #
        tablename = "stdm_job_title"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_TYPE = T("Create Officer Rank")
        crud_strings[tablename] = Storage(
            label_create = ADD_TYPE,
            title_display = T("Officer Rank"),
            title_list = T("Officer Ranks"),
            title_update = T("Edit Officer Rank"),
            label_list_button = T("List Officer Ranks"),
            label_delete_button = T("Delete Officer Rank"),
            msg_record_created = T("Officer Rank added"),
            msg_record_modified = T("Officer Rank updated"),
            msg_record_deleted = T("Officer Rank deleted"),
            msg_list_empty = T("No Officer Ranks currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        job_title_id = S3ReusableField("job_title_id", "reference %s" % tablename,
                                       requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "stdm_job_title.id",
                                                              represent,
                                                              sort=True)),
                                       represent=represent,
                                       label=T("Officer Rank"),
                                       ondelete="RESTRICT",
                                       comment = S3PopupLink(c = "stdm",
                                                             f = "job_title",
                                                             label = ADD_TYPE,
                                                             ),
                                       )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Planners
        #
        tablename = "stdm_planner"
        define_table(tablename,
                     person_id(
                        requires = IS_ADD_PERSON_WIDGET2(),
                        widget = S3AddPersonWidget2(controller="stdm"),
                     ),
                     job_title_id(),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Planner"),
            title_display = T("Planner"),
            title_list = T("Planners"),
            title_update = T("Edit Planner"),
            label_list_button = T("List Planners"),
            label_delete_button = T("Delete Planner"),
            msg_record_created = T("Planner added"),
            msg_record_modified = T("Planner updated"),
            msg_record_deleted = T("Planner deleted"),
            msg_list_empty = T("No Planners currently registered"))

        # ---------------------------------------------------------------------
        # Surveyors
        #
        tablename = "stdm_surveyor"
        define_table(tablename,
                     person_id(
                        requires = IS_ADD_PERSON_WIDGET2(),
                        widget = S3AddPersonWidget2(controller="stdm"),
                     ),
                     job_title_id(),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Surveyor"),
            title_display = T("Surveyor"),
            title_list = T("Surveyors"),
            title_update = T("Edit Surveyor"),
            label_list_button = T("List Surveyors"),
            label_delete_button = T("Delete Surveyor"),
            msg_record_created = T("Surveyor added"),
            msg_record_modified = T("Surveyor updated"),
            msg_record_deleted = T("Surveyor deleted"),
            msg_list_empty = T("No Surveyors currently registered"))

        # ---------------------------------------------------------------------
        # (Local Government) Surveys
        #

        tablename = "stdm_gov_survey"
        define_table(tablename,
                     # Foreign Key
                     super_link("spatial_unit_id", "stdm_spatial_unit",
                                instance_types = Storage(stdm_parcel = T("Parcel"),
                                                         ),
                                label = T("Parcel"),
                                readable = True,
                                represent = S3Represent("stdm_spatial_unit"),
                                updateable = True,
                                writable = True,
                                ),
                     s3_date(label = T("Date of Survey")),
                     person_id("surveyor",
                               label = T("Surveyor"),
                               # @ToDo: Fix multiple Widgets in a form!
                               #requires = IS_ADD_PERSON_WIDGET2(),
                               # @ToDo: Filter to Surveyors
                               #widget = S3AddPersonWidget2(controller="stdm"),
                               ),
                     person_id("planner",
                               label = T("Planner"),
                               #requires = IS_ADD_PERSON_WIDGET2(),
                               # @ToDo: Filter to Planners
                               #widget = S3AddPersonWidget2(controller="stdm"),
                               ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Survey"),
            title_display = T("Survey"),
            title_list = T("Surveys"),
            title_update = T("Edit Survey"),
            label_list_button = T("List Surveys"),
            label_delete_button = T("Delete Survey"),
            msg_record_created = T("Survey added"),
            msg_record_modified = T("Survey updated"),
            msg_record_deleted = T("Survey deleted"),
            msg_list_empty = T("No Surveys currently registered"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class S3RuralAgricultureModel(S3Model):

    """ Rural Agriculture Profile """

    names = ("stdm_garden",
             "stdm_farmer",
             "stdm_socioeconomic_impact",
             "stdm_input_service",
             "stdm_farmer_socioeconomic_impact",
             "stdm_farmer_input_service",
             "stdm_rural_survey",
             )

    def model(self):

        T = current.T
        db = current.db

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        person_id = self.pr_person_id

        # ---------------------------------------------------------------------
        # Gardens
        #
        tablename = "stdm_garden"
        define_table(tablename,
                     # Instance
                     self.super_link("spatial_unit_id", "stdm_spatial_unit"),
                     Field("name",
                           label = T("Code"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     self.gis_location_id(
                         widget = S3LocationSelector(catalog_layers = True,
                                                     points = True,
                                                     polygons = True,
                                                     ),
                     ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Garden"),
            title_display = T("Garden"),
            title_list = T("Gardens"),
            title_update = T("Edit Garden"),
            label_list_button = T("List Gardens"),
            label_delete_button = T("Delete Garden"),
            msg_record_created = T("Garden added"),
            msg_record_modified = T("Garden updated"),
            msg_record_deleted = T("Garden deleted"),
            msg_list_empty = T("No Gardens currently registered"))

        configure(tablename,
                  super_entity = "stdm_spatial_unit",
                  )

        # ---------------------------------------------------------------------
        # Farmers
        #
        tablename = "stdm_farmer"
        define_table(tablename,
                     person_id(
                        requires = IS_ADD_PERSON_WIDGET2(),
                        widget = S3AddPersonWidget2(controller="stdm"),
                     ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_TYPE = T("Create Farmer")
        crud_strings[tablename] = Storage(
            label_create = ADD_TYPE,
            title_display = T("Farmer"),
            title_list = T("Farmers"),
            title_update = T("Edit Farmer"),
            label_list_button = T("List Farmers"),
            label_delete_button = T("Delete Farmer"),
            msg_record_created = T("Farmer added"),
            msg_record_modified = T("Farmer updated"),
            msg_record_deleted = T("Farmer deleted"),
            msg_list_empty = T("No Farmers currently registered"))

        crud_form = S3SQLCustomForm("person_id",
                                    S3SQLInlineLink("socioeconomic_impact",
                                                    field = "socioeconomic_impact_id",
                                                    label = T("Socio-economic Impacts"),
                                                    ),
                                    S3SQLInlineLink("input_service",
                                                    field = "input_service_id",
                                                    label = T("Input Services"),
                                                    ),
                                    "comments",
                                    )

        list_fields = ["person_id$first_name",
                       "person_id$middle_name",
                       "person_id$last_name",
                       (T("National ID"), "person_id$national_id.value"),
                       "person_id$gender",
                       "person_id$date_of_birth",
                       "person_id$person_details.marital_status",
                       (T("Telephone"), "person_id$phone.value"),
                       (T("Address"), "person_id$address.location_id$addr_street"),
                       (T("Socio-economic Impacts"), "socioeconomic_impact__link.socioeconomic_impact_id"),
                       (T("Input Services"), "input_service__link.input_service_id"),
                       ]

        configure(tablename,
                  crud_form = crud_form,
                  list_fields = list_fields,
                  )

        self.add_components(tablename,
                            pr_address = {"link": "pr_person",
                                          "joinby": "id",
                                          "key": "pe_id",
                                          "fkey": "pe_id",
                                          "pkey": "person_id",
                                          },
                            stdm_socioeconomic_impact = {"link": "stdm_farmer_socioeconomic_impact",
                                                         "joinby": "farmer_id",
                                                         "key": "socioeconomic_impact_id",
                                                         #"actuate": "replace",
                                                         },
                            stdm_input_service = {"link": "stdm_farmer_input_service",
                                                  "joinby": "farmer_id",
                                                  "key": "input_service_id",
                                                  #"actuate": "replace",
                                                  },
                            )

        represent = S3Represent(lookup=tablename, fields=["person_id"])
        farmer_id = S3ReusableField("farmer_id", "reference %s" % tablename,
                                    requires = IS_EMPTY_OR(
                                               IS_ONE_OF(db, "stdm_farmer.id",
                                                         represent,
                                                         sort=True)),
                                    represent=represent,
                                    label=T("Farmer"),
                                    ondelete="CASCADE",
                                    comment = S3PopupLink(c = "stdm",
                                                          f = "farmer",
                                                          label = ADD_TYPE,
                                                          ),
                                    )

        # ---------------------------------------------------------------------
        # Socio-economic Impacts
        #
        tablename = "stdm_socioeconomic_impact"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_TYPE = T("Create Socio-economic Impact")
        crud_strings[tablename] = Storage(
            label_create = ADD_TYPE,
            title_display = T("Socio-economic Impact"),
            title_list = T("Socio-economic Impacts"),
            title_update = T("Edit Socio-economic Impact"),
            label_list_button = T("List Socio-economic Impacts"),
            label_delete_button = T("Delete Socio-economic Impact"),
            msg_record_created = T("Socio-economic Impact added"),
            msg_record_modified = T("Socio-economic Impact updated"),
            msg_record_deleted = T("Socio-economic Impact deleted"),
            msg_list_empty = T("No Socio-economic Impacts currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        socioeconomic_impact_id = S3ReusableField("socioeconomic_impact_id", "reference %s" % tablename,
                                                  requires = IS_EMPTY_OR(
                                                             IS_ONE_OF(db, "stdm_socioeconomic_impact.id",
                                                                       represent,
                                                                       sort=True)),
                                                  represent=represent,
                                                  label=T("Socio-economic Impact"),
                                                  ondelete="CASCADE",
                                                  comment = DIV(_class="tooltip",
                                                         _title="%s|%s" % (T("Socio-economic Impact"),
                                                                           T("The socio-economic impact on the farmer"),
                                                                           )),
                                                  #comment = S3PopupLink(c = "stdm",
                                                  #                      f = "socioeconomic_impact",
                                                  #                      label = ADD_TYPE,
                                                  #                      ),
                                                  )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Input Services
        #
        tablename = "stdm_input_service"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        ADD_TYPE = T("Create Input Service")
        crud_strings[tablename] = Storage(
            label_create = ADD_TYPE,
            title_display = T("Input Service"),
            title_list = T("Input Services"),
            title_update = T("Edit Input Service"),
            label_list_button = T("List Input Services"),
            label_delete_button = T("Delete Input Service"),
            msg_record_created = T("Input Service added"),
            msg_record_modified = T("Input Service updated"),
            msg_record_deleted = T("Input Service deleted"),
            msg_list_empty = T("No Input Services currently registered"))

        represent = S3Represent(lookup=tablename, translate=True)
        input_service_id = S3ReusableField("input_service_id", "reference %s" % tablename,
                                           requires = IS_EMPTY_OR(
                                                      IS_ONE_OF(db, "stdm_input_service.id",
                                                                represent,
                                                                sort=True)),
                                           represent=represent,
                                           label=T("Input Service"),
                                           ondelete="CASCADE",
                                           comment = DIV(_class="tooltip",
                                                         _title="%s|%s" % (T("Input Service"),
                                                                           T("The input service that is given a priority rank"),
                                                                           )),
                                           #comment = S3PopupLink(c = "stdm",
                                           #                      f = "input_service",
                                           #                      label = ADD_TYPE,
                                           #                      ),
                                           )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # ---------------------------------------------------------------------
        # Farmers <> Socio-economic Impacts
        #
        tablename = "stdm_farmer_socioeconomic_impact"
        define_table(tablename,
                     farmer_id(empty = False),
                     socioeconomic_impact_id(empty = False),
                     *s3_meta_fields()
                     )

        # ---------------------------------------------------------------------
        # Farmers <> Input Services
        #
        tablename = "stdm_farmer_input_service"
        define_table(tablename,
                     farmer_id(empty = False),
                     input_service_id(empty = False),
                     *s3_meta_fields()
                     )

        # ---------------------------------------------------------------------
        # (Rural) Surveys
        #

        role_opts = {1: "Child of Farmer",
                     2: "Farm Manager",
                     3: "Laborer",
                     4: "Smallholder Farmer",
                     5: "Spouse",
                     }

        relationship_opts = {1: "Friend",
                             2: "Neighbour",
                             3: "Administrative Unit Leader",
                             }

        tablename = "stdm_rural_survey"
        define_table(tablename,
                     # Foreign Key
                     #self.super_link("spatial_unit_id", "stdm_spatial_unit"),
                     s3_date(label = T("Enumeration Date")),
                     person_id("enumerator",
                               label = T("Enumerator"),
                               # @ToDo: Fix multiple Widgets in a form!
                               #requires = IS_ADD_PERSON_WIDGET2(),
                               #widget = S3AddPersonWidget2(controller="stdm"),
                               ),
                     person_id("respondent",
                               label = T("Respondent"),
                               #requires = IS_ADD_PERSON_WIDGET2(),
                               #widget = S3AddPersonWidget2(controller="stdm"),
                               ),
                     Field("role", "integer",
                           label = T("Respondent Role"),
                           represent = S3Represent(options = role_opts),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(role_opts)
                                        ),
                           ),
                     person_id("witness",
                               label = T("Witness"),
                               #requires = IS_ADD_PERSON_WIDGET2(),
                               #widget = S3AddPersonWidget2(controller="stdm"),
                               ),
                     Field("relationship", "integer",
                           label = T("Witness Relationship"),
                           represent = S3Represent(options = relationship_opts),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(relationship_opts)
                                        ),
                           ),
                     s3_comments(),
                     *s3_meta_fields()
                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Survey"),
            title_display = T("Survey"),
            title_list = T("Surveys"),
            title_update = T("Edit Survey"),
            label_list_button = T("List Surveys"),
            label_delete_button = T("Delete Survey"),
            msg_record_created = T("Survey added"),
            msg_record_modified = T("Survey updated"),
            msg_record_deleted = T("Survey deleted"),
            msg_list_empty = T("No Surveys currently registered"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
def stdm_rheader(r):
    """ Resource Header for Social Tenure Domain Model """

    if r.representation != "html":
        return None

    s3db = current.s3db
    tablename, record = s3_rheader_resource(r)
    if tablename != r.tablename:
        resource = s3db.resource(tablename, id=record.id)
    else:
        resource = r.resource

    rheader = None
    rheader_fields = []

    if record:
        T = current.T

        if tablename == "pr_person":

            tabs = ((T("Basic Details"), None),
                    (T("Identity"), "identity"),
                    (T("Address"), "address"),
                    (T("Contacts"), "contacts"),
                    (T("Groups"), "group_membership"),
                    (T("Tenures"), "tenure_relationship"),
                    )

            rheader_fields = (["first_name"],
                              ["middle_name"],
                              ["last_name"],
                              ["gender"],
                              ["date_of_birth"],
                              )

        elif tablename == "pr_group":

            tabs = ((T("Basic Details"), None),
                    (T("Address"), "address"),
                    (T("Contacts"), "contact"),
                    (T("Members"), "group_membership"),
                    (T("Tenures"), "tenure_relationship"),
                    )

            rheader_fields = [["name"],
                              ["comments"],
                              ]

        elif tablename == "gis_location":

            tabs = ((T("Basic Details"), None),
                    (T("Local Names"), "name"),
                    (T("Alternate Names"), "name_alt"),
                    (T("Key Value pairs"), "tag"),
                    )

            rheader_fields = [["name"],
                              ]

            if record.level:
                rheader_fields.append(["level"])
            else:
                tabs.append((T("Tenures"), "tenure"))

        elif tablename == "stdm_tenure":

            tabs = ((T("Basic Details"), None),
                    (T("Documents"), "document"),
                    )

            rheader_fields = (["spatial_unit_id"],
                              )

        elif tablename == "stdm_farmer":

            tabs = ((T("Basic Details"), None),
                    #(T("Identity"), "identity"),
                    #(T("Address"), "address"),
                    #(T("Contacts"), "contacts"),
                    #(T("Groups"), "group_membership"),
                    #(T("Tenures"), "tenure_relationship"),
                    )

            rheader_fields = (["spatial_unit_id"],
                              )

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table = resource.table,
                                                         record = record,
                                                         )

    return rheader

# END =========================================================================
