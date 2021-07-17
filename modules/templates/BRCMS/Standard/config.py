# -*- coding: utf-8 -*-

# =============================================================================
def config(settings):
    """
        BRCMS: Sahana Beneficiary Registry and Case Management System
    """

    # PrePopulate data
    settings.base.prepopulate.append("BRCMS/Standard")
    settings.base.prepopulate_demo.append("BRCMS/Standard/Demo")

# END =========================================================================
