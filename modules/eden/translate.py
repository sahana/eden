# -*- coding: utf-8 -*-

# mandatory __all__ statement:
#
# - all classes in the name list will be initialized with the
#   module prefix as only parameter. Subclasses of S3Model
#   support this automatically, and run the model() method
#   if the module is enabled in deployment_settings, otherwise
#   the default() method.
#
# - all other names in the name list will be added to response.s3
#   if their names start with the module prefix plus underscore
#
__all__ = ["S3TranslateModel"]

# The folloing import statements are needed in every model
# (you may need more than this in your particular case). To
# import classes from s3, use from + relative path like below
#
from gluon import *
from gluon.storage import Storage
from ..s3 import *
from eden.layouts import S3AddResourceLink
import os

# =============================================================================
# Define a new class as subclass of S3Model
# => you can define multiple of these classes within the same module, each
#    of them will be initialized only when one of the declared names gets
#    requested from s3db
# => remember to list all model classes in __all__, otherwise they won't ever
#    be loaded.
#
class S3TranslateModel(S3Model):

    # Declare all the names this model can auto-load, i.e. all tablenames
    # and all response.s3 names which are defined here. If you omit the "names"
    # variable, then this class will serve as a fallback model for this module
    # in case a requested name cannot be found in one of the other model classes
    #
    names = ["translate_language"]

    def model(self):

        db = current.db
        T = current.T

        s3 = current.response.s3
        s3db = current.s3db
        settings = current.deployment_settings

        tablename = "translate_language"

        table = self.define_table(tablename,
                                  Field("code",notnull=True,
                                         length=10,
 					 label = T("Language code")),
                                  Field("file","upload",
                                        label = T("Translated File")),
				  *s3.meta_fields()
				 )

        self.configure(tablename,
                       onaccept = self.translate_language_onaccept,
                       )

        # Return names to response.s3
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Return safe defaults for model globals, this will be called instead
            of model() in case the model has been deactivated in
            deployment_settings.

            You don't need this function in case your model is mandatory anyway.
        """

        return Storage()

    # ---------------------------------------------------------------------
    @staticmethod
    def translate_language_onaccept(form):

        """ Receive the uploaded csv file """

	from ..s3.s3translate import CsvToWeb2py

	base_dir = os.path.join(os.getcwd(), "applications", current.request.application)
	upload_folder = os.path.join(base_dir,"uploads")

	csvfilelist = []
        csvfilename = os.path.join(base_dir,upload_folder,form.vars.file)
        csvfilelist.append(csvfilename)
	code = form.vars.code
	C = CsvToWeb2py()

        C.convert_to_w2p(csvfilelist,code+".py","m")

        return

# =============================================================================
# Module-global functions will automatically be added to response.s3 if
# they use the module prefix and are listed in __all__
#
# Represents are good to put here as they can be put places without loading the
# models at that time
#
#def skeleton_example_represent(id):

    # Your function may need to access tables. If a table isn't defined
    # at the point when this function gets called, then this:
#   s3db = current.s3db
#   skeleton_table = s3db.skeleton_table
#   # will load the table. This is the same function as self.table described in
    # the model class except that "self" is not available here, so you need to
    # use the class instance as reference instead

#   db = current.db
#   query = (table.id == id)
#   record = db(query).select(table.name,
#                             limitby=(0, 1)).first()
#   if record:
#       return record.name
#   else:
#       return current.messages.NONE

# END =========================================================================
