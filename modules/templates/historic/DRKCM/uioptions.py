# -*- coding: utf-8 -*-

"""
    Org-specific UI Options for DRKCM template

    @license: MIT
"""

from gluon import current

# =============================================================================
# Default UI options
#
UI_DEFAULTS = {#"case_arrival_date_label": "Date of Entry",
               "case_collaboration": False,
               "case_document_templates": False,
               "case_header_protection_themes": False,
               "case_hide_default_org": False,
               "case_use_response_tab": True,
               "case_use_photos_tab": False,
               "case_use_bamf": False,
               "case_use_address": True,
               "case_use_appointments": False,
               "case_use_education": False,
               "case_use_flags": False,
               "case_use_notes": False,
               "case_use_occupation": True,
               "case_use_pe_label": False,
               "case_use_place_of_birth": False,
               "case_use_residence_status": True,
               "case_use_referral": True,
               "case_use_service_contacts": False,
               "case_lodging": None, # "site"|"text"|None
               "case_lodging_dates": False,
               "case_nationality_mandatory": False,
               "case_show_total_consultations": True,
               "activity_closure": True,
               "activity_comments": True,
               "activity_use_sector": True,
               "activity_need_details": True,
               "activity_follow_up": False,
               "activity_priority": False,
               "activity_pss_vulnerability": True,
               "activity_use_need": False,
               #"activity_tab_label": "Counseling Reasons",
               "appointments_staff_link": False,
               "appointments_use_organizer": False,
               "response_activity_autolink": False,
               "response_due_date": False,
               "response_effort_required": True,
               "response_planning": False,
               "response_tab_need_filter": False,
               "response_themes_details": False,
               "response_themes_sectors": False,
               "response_themes_needs": False,
               "response_themes_optional": False,
               "response_types": True,
               "response_use_organizer": False,
               "response_use_time": False,
               "response_performance_indicators": None, # default
               }

# =============================================================================
# Custom options sets
#
UI_OPTIONS = {"LEA": {"case_arrival_date_label": "Date of AKN",
                      "case_collaboration": True,
                      "case_document_templates": True,
                      "case_header_protection_themes": True,
                      "case_hide_default_org": True,
                      "case_use_response_tab": True,
                      "case_use_photos_tab": True,
                      "case_use_bamf": True,
                      "case_use_address": False,
                      "case_use_appointments": False,
                      "case_use_education": True,
                      "case_use_flags": False,
                      "case_use_notes": False,
                      "case_use_occupation": False,
                      "case_use_pe_label": True,
                      "case_use_place_of_birth": True,
                      "case_use_residence_status": False,
                      "case_use_referral": False,
                      "case_use_service_contacts": False,
                      "case_lodging": "site",
                      "case_lodging_dates": False,
                      "case_nationality_mandatory": True,
                      "case_show_total_consultations": False,
                      "activity_closure": False,
                      "activity_comments": False,
                      "activity_use_sector": False,
                      "activity_need_details": False,
                      "activity_follow_up": False,
                      "activity_priority": True,
                      "activity_pss_vulnerability": False,
                      "activity_use_need": True,
                      #"activity_tab_label": "Counseling Reasons",
                      "appointments_staff_link": True,
                      "appointments_use_organizer": True,
                      "response_activity_autolink": True,
                      "response_due_date": False,
                      "response_effort_required": True,
                      "response_planning": False,
                      "response_tab_need_filter": True,
                      "response_themes_details": True,
                      "response_themes_sectors": True,
                      "response_themes_needs": True,
                      "response_themes_optional": True,
                      "response_types": False,
                      "response_use_organizer": True,
                      "response_use_time": True,
                      "response_performance_indicators": "lea",
                      },
              }

# =============================================================================
# Option sets per Org
#
UI_TYPES = {"LEA Ellwangen": "LEA",
            "Ankunftszentrum Heidelberg": "LEA",
            }

# =============================================================================
# Getters
#
def get_ui_options():
    """ Get the UI options for the current user's root organisation """

    ui_options = dict(UI_DEFAULTS)
    ui_type = UI_TYPES.get(current.auth.root_org_name())
    if ui_type:
        ui_options.update(UI_OPTIONS[ui_type])
    return ui_options

def get_ui_option(key):
    """ Getter for UI options, for lazy deployment settings """

    def getter(default=None):
        return get_ui_options().get(key, default)
    return getter

# END =========================================================================
