# -*- coding: utf-8 -*-

""" Sahana Eden UAV Image Management

    @copyright: 2016 (c) Sahana Software Foundation
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

__all__ = ("UAVModel",
           )

from gluon import *
from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class UAVModel(S3Model):
    """ Model for UAV """

    names = ("uav_manufacturer",
             "uav_model",
             "uav_dataset",
             "uav_data",
             )

    def model(self):

        db = current.db
        T = current.T
        s3 = current.response.s3

        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure

        # ---------------------------------------------------------------------
        # UAV Manufacturer
        # Hardware Manufacturer only
        tablename = "uav_manufacturer"
        define_table(tablename,
                     Field("name", unique=True,
                           label = T("Name of the Manufacturer"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("country", length=2,
                           label = T("Country"),
                           represent = self.gis_country_code_represent,
                           requires = IS_EMPTY_OR(IS_IN_SET_LAZY(
                                                    lambda: current.gis.get_countries(key_type="code"),
                                                    zero=current.messages.SELECT_LOCATION)),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        manufacturer_represent = S3Represent(lookup = tablename, translate=True)

        manufacturer_id = S3ReusableField("manufacturer_id", "reference %s" % tablename,
                                          label = T("UAV Manufacturer"),
                                          ondelete = "CASCADE",
                                          represent = manufacturer_represent,
                                          requires = IS_EMPTY_OR(
                                                        IS_ONE_OF(db, "uav_manufacturer.id",
                                                                  manufacturer_represent)
                                                                 )
                                          )

        # CRUD Strings
        crud_strings[tablename] = Storage(
                    label_create = T("Add Manufacturer"),
                    title_display = T("UAV Manufacturer"),
                    title_list = T("UAV Manufacturers"),
                    title_update = T("Edit Manufacturer data"),
                    subtitle_list = T("List UAV Manufacturers"),
                    label_list_button = T("List UAV Manufacturers"),
                    label_delete_button = T("Delete this manufacturer record"),
                    msg_record_created = T("New Manufacturer added"),
                    msg_record_modified = T("Manufacturer record updated"),
                    msg_record_deleted = T("Manufacturer record deleted"),
                    msg_list_empty = T("No Manufacturer available"))

        # ---------------------------------------------------------------------
        # UAV Model
        tablename = "uav_model"
        define_table(tablename,
                     manufacturer_id(),
                     Field("name",
                           label = T("Model Name/Number"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD Strings
        crud_strings[tablename] = Storage(
                    label_create = T("Add Model"),
                    title_display = T("UAV Model"),
                    title_list = T("UAV Models"),
                    title_update = T("Edit model"),
                    subtitle_list = T("List UAV Models"),
                    label_list_button = T("List UAV Models"),
                    label_delete_button = T("Delete this model record"),
                    msg_record_created = T("New Model added"),
                    msg_record_modified = T("Model record updated"),
                    msg_record_deleted = T("Model record deleted"),
                    msg_list_empty = T("No Model for this manufacturer available"))

        uav_model_represent = S3Represent(tablename, translate=True)

        configure(tablename,
                  deduplicate = S3Duplicate(primary=("manufacturer_id", "name",)),
                  )

        # ---------------------------------------------------------------------
        # UAV DATASETS
        tablename = "uav_dataset"
        define_table(tablename,
                     self.project_project_id(empty = True,
                                             ),
                     Field("name", unique=True,
                           label = T("Name for Dataset"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     manufacturer_id(script = '''
$.filterOptionsS3({
    'trigger':'manufacturer_id',
    'target':'model',
    'lookupPrefix': 'uav',
    'lookupResource':'model',
    'optional': true
})'''
                     ),
                     Field("model", "reference uav_model",
                           label = T("Model"),
                           represent = uav_model_represent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "uav_model.id",
                                                  uav_model_represent
                                                  ),
                                        ),
                           ),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create New Dataset"),
            title_display = T("UAV Dataset"),
            title_list = T("Datasets"),
            title_update = T("Edit Dataset"),
            label_list_button = T("List Datasets"),
            msg_record_created = T("Dataset added"),
            msg_record_modified = T("Dataset updated"),
            msg_record_deleted = T("Dataset deleted"),
            msg_list_empty = T("No Dataset present!")
        )

        dataset_represent = S3Represent(lookup = tablename,
                                        fields = ["name", "manufacturer_id",],
                                        field_sep = " - ")

        dataset_id = S3ReusableField("dataset_id", "reference %s" % tablename,
                                     label = T("Dataset"),
                                     ondelete = "CASCADE",
                                     represent = dataset_represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "uav_dataset.id",
                                                              dataset_represent)),
                                   )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return {}

# END =========================================================================
