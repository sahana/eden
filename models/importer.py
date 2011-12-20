# -*- coding: utf-8 -*-

"""
    Importer

    @author: Shikhar Kohli
"""

module = "importer"
if deployment_settings.has_module(module):

    resourcename = "spreadsheet"
    tablename = module + "_" + resourcename
    table = db.define_table(tablename,
                            Field("name", required=True, notnull=True),
                            Field("path", type="upload", uploadfield=True, required=True, notnull=True),
                            s3_comments(),
                            Field("json", writable=False, readable=False),

                            *(s3_timestamp() + s3_uid()))

    table.name.comment = DIV(_class = "tooltip",
                             _title = T("Name") + "|" + T("Enter a name for the spreadsheet you are uploading."))

    s3.crud_strings[tablename]= Storage(
            title_create = T("Upload a Spreadsheet"),
            title_list = T("List of Spreadsheets uploaded"),
            label_list_button = T("List of Spreadsheets"),
            #msg_record_created = T("Spreadsheet uploaded")
            )
### TEMP TESTING CODE NOT USED

    resourcename = "csv"
    tablename = module + "_" + resourcename
    table = db.define_table( tablename,
                             Field("controller",
                                   readable=True, # Just shows up in List View
                                   writable=True,
                                   ),
                             Field("function",
                                   readable=True, # Just shows up in List View
                                   writable=True,
                                   ),
                             Field("filename",
                                   readable=True, # Just shows up in List View
                                   writable=True,
                                   ),
                             Field("file",
                                   "upload",
                                   autodelete=True,
                                   uploadfolder = os.path.join(request.folder,
                                                               "uploads",
                                                               "imports"),
                                   comment = DIV( _class="tooltip",
                                                  _title="%s|%s" % (T("Import File"),
                                                                    T("Upload a CSV file formatted according to the Template."))),
                                   label = T("Import File")),
                             Field("job_id",
                                   length=128,
                                   unique=True,
                                   readable=False,
                                   writable=False,
                                   ),

                             *s3_timestamp()
                           )

    s3.crud_strings[tablename]= Storage(
            title_create = T("Upload a CSV file"),
            title_list = T("List of CSV files uploaded"),
            label_list_button = T("List of CSV files"),
            )
### END OF TEMP TESTING CODE NOT USED
