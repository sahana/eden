# -*- coding: utf-8 -*-

""" Sahana Eden Translate Model

    @copyright: 2012-13 (c) Sahana Software Foundation
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

__all__ = ["S3TranslateModel"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3TranslateModel(S3Model):

    names = ["translate_language",
             "translate_percentage",
             ]

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
        table = define_table(tablename,
                             Field("code", length=10, notnull=True,
                                   requires = IS_IN_SET(langlist),
                                   label = T("Language Code")),
                             Field("file", "upload", notnull=True,
                                   label = T("Translated File")),
                             *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            title_create = T("Upload file"),
            msg_record_created = T("File uploaded"))

        self.configure(tablename,
                       onaccept = self.translate_language_onaccept,
                       )

        #---------------------------------------------------------------------
        # Translation Status
        #
        tablename = "translate_percentage"
        table = define_table(tablename,
                             Field("code", length=10, notnull=True),
                             Field("module", length=32, notnull=True),
                             Field("translated", "integer"),
                             Field("untranslated", "integer"),
                             Field("dirty", "boolean", default=False),
                             *s3_meta_fields())

        #----------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def translate_language_onaccept(form):
        """
            Merge the uploaded CSV file with existing language file
            & mark translation percentages as dirty
        """

        import os
        from ..s3.s3translate import CsvToWeb2py

        vars = form.vars
        code = vars.code

        # Merge the existing translations with the new translations
        csvfilename = os.path.join(current.request.folder, "uploads",
                                   vars.file)
        csvfilelist = [csvfilename]
        C = CsvToWeb2py()
        C.convert_to_w2p(csvfilelist, "%s.py" % code, "m")

        # Mark the percentages as dirty
        ptable = current.s3db.translate_percentage
        current.db(ptable.code == code).update(dirty=True)

        return

# END =========================================================================
