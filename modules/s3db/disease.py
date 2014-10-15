# -*- coding: utf-8 -*-

__all__ = ("CaseModel",
           )

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3AddResourceLink

# =============================================================================
class CaseModel(S3Model):

    def model(self):

        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():

        return dict()

# END =========================================================================
