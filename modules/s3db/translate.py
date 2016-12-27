# -*- coding: utf-8 -*-

""" Sahana Eden Translate Model

    @copyright: 2012-2016 (c) Sahana Software Foundation
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

__all__ = ("S3TranslateModel",)

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3TranslateModel(S3Model):

    names = ("translate_language",
             "translate_percentage",
             )

    def model(self):

        T = current.T
        define_table = self.define_table

        #---------------------------------------------------------------------
        # Translated CSV files
        #
        from ..s3.s3translate import TranslateAPI

        langlist = TranslateAPI.get_langcodes()
        langlist.sort()

        tablename = "translate_language"
        define_table(tablename,
                     Field("code", length=10, notnull=True,
                           label = T("Language Code"),
                           requires = IS_IN_SET(langlist),
                           ),
                     Field("file", "upload", notnull=True,
                           label = T("Translated File"),
                           length = current.MAX_FILENAME_LENGTH,
                           requires = IS_UPLOAD_FILENAME(
                                          extension = "csv",
                                          error_message = T("CSV file required")),
                           ),
                     *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Upload file"),
            msg_record_created = T("File uploaded"))

        self.configure(tablename,
                       onaccept = self.translate_language_onaccept,
                       onvalidation = self.translate_language_onvalidation,
                       )

        #---------------------------------------------------------------------
        # Translation Status
        #
        tablename = "translate_percentage"
        define_table(tablename,
                     Field("code", length=10, notnull=True),
                     Field("module", length=32, notnull=True),
                     Field("translated", "integer"),
                     Field("untranslated", "integer"),
                     Field("dirty", "boolean", default=False),
                     *s3_meta_fields())

        #----------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def translate_language_onvalidation(form):
        """
            Check CSV file before upload
        """

        import csv

        T = current.T
        try:
            csvfile = form.vars.file.file
        except:
            form.errors["file"] = T("No file uploaded.")
            return
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
        except csv.Error:
            error = T("Error reading file (invalid format?): %(msg)s")
            import sys
            form.errors["file"] = error % {"msg": sys.exc_info()[1]}
        csvfile.seek(0)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def translate_language_onaccept(form):
        """
            Merge the uploaded CSV file with existing language file
            & mark translation percentages as dirty
        """

        import csv
        import os
        from ..s3.s3translate import Strings

        form_vars = form.vars
        lang_code = form_vars.code

        # Merge the existing translations with the new translations
        csvfilename = os.path.join(current.request.folder, "uploads",
                                   form_vars.file)
        S = Strings()
        try:
            S.write_w2p([csvfilename], lang_code, "m")
        except (csv.Error, SyntaxError):
            import sys
            current.session.error = \
                current.T("Error reading file (invalid format?): %(msg)s") % \
                {"msg": sys.exc_info()[1]}
            return

        # Mark the percentages as dirty
        ptable = current.s3db.translate_percentage
        current.db(ptable.code == lang_code).update(dirty=True)

        return

# END =========================================================================
