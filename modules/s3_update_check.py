# -*- coding: utf-8 -*-

import os

def update_check(environment, template="default"):
    """
        Check whether the dependencies are sufficient to run Eden

        @ToDo: Integrate into WebSetup:
               http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/WebSetup
    """

    # Get Web2py environment into our globals.
    globals().update(**environment)

    app_path = os.path.join("applications", request.application)

    # Fatal errors
    errors = []
    # Non-fatal warnings
    warnings = []

    # -------------------------------------------------------------------------
    # Check Python libraries
    try:
        import dateutil
    except(ImportError):
        errors.append("S3 unresolved dependency: dateutil required for Sahana to run")
    try:
        import lxml
    except(ImportError):
        errors.append("S3XML unresolved dependency: lxml required for Sahana to run")
    try:
        import shapely
    except(ImportError):
        warnings.append("S3GIS unresolved dependency: shapely required for GIS support")
    try:
        import xlrd
    except(ImportError):
        warnings.append("S3XLS unresolved dependency: xlrd required for XLS import")
    try:
        import xlwt
    except(ImportError):
        warnings.append("S3XLS unresolved dependency: xlwt required for XLS export")
    try:
        from PIL import Image
    except(ImportError):
        try:
            import Image
        except(ImportError):
            warnings.append("S3PDF unresolved dependency: Python Imaging required for PDF export")
    try:
        import reportlab
    except(ImportError):
        warnings.append("S3PDF unresolved dependency: reportlab required for PDF export")
    try:
        import matplotlib
    except(ImportError):
        warnings.append("S3Chart unresolved dependency: matplotlib required for charting")
    try:
        import numpy
    except(ImportError):
        warnings.append("S3Cube unresolved dependency: numpy required for pivot table reports")
    try:
        import tweepy
    except(ImportError):
        warnings.append("S3Msg unresolved dependency: tweepy required for non-Tropo Twitter support")
    try:
        import PyRTF
    except(ImportError):
        warnings.append("Survey unresolved dependency: PyRTF required if you want to export assessment templates as a Word document")

    # -------------------------------------------------------------------------
    # Check Web2Py version
    #
    # Currently, the minimum usable Web2py is determined by the existence of
    # the global "current".
    try:
        from gluon import current
    except ImportError:
        errors.append(
            "The installed version of Web2py is too old -- it does not define current."
            "\nPlease upgrade Web2py to a more recent version.")

    # We also warn if the Scheduler is available
    web2py_minimum_version = "Version 1.99.2 (2011-09-26 00:51:34) stable"
    web2py_version_ok = True
    try:
        from gluon.fileutils import parse_version
    except ImportError:
        web2py_version_ok = False
    if web2py_version_ok:
        web2py_minimum_datetime = parse_version(web2py_minimum_version)[3]
        web2py_installed_datetime = request.global_settings.web2py_version[3]
        web2py_version_ok = web2py_installed_datetime >= web2py_minimum_datetime
    if not web2py_version_ok:
        warnings.append(
            "The installed version of Web2py is too old to provide the Scheduler,"
            "\nso scheduled tasks will not be available. If you need scheduled tasks,"
            "\nplease upgrade Web2py to at least version: %s" % \
            web2py_minimum_version)

    # -------------------------------------------------------------------------
    # Create required directories if needed
    databases_dir = os.path.join(app_path, "databases")
    try:
        os.stat(databases_dir)
    except OSError:
        # not found, create it
        os.mkdir(databases_dir)

    # -------------------------------------------------------------------------
    # Copy in Templates
    # - currently 000_config.py
    #
    # To change which folder is used to source the file(s), create a
    # file models/0000_update_check.py with TEMPLATE = "foldername"
    #
    # @ToDo: Add:
    #        - Theme: CSS, views/layout.html, modules/eden/layouts.py
    #        - Menus: modules/eden/menus.py, models/01_menu.py
    #        - Parser for Inbound messages: http://eden.sahanafoundation.org/wiki/BluePrint/Messaging/CERTSMSParsing

    template_folder = os.path.join(app_path, "private", "templates")
    
    template_files = {
        # source : destination
        "000_config.py" : os.path.join("models", "000_config.py"),
    }

    copied_from_template = []

    for t in template_files:
        src_path = os.path.join(template_folder, template, t)
        dst_path = os.path.join(app_path, template_files[t])
        try:
            os.stat(dst_path)
        except OSError:
            # Not found, copy from template
            if t == "000_config.py":
                input = open(src_path)
                output = open(dst_path, "w")
                for line in input:
                    if "akeytochange" in line:
                        # Generate a random hmac_key to secure the passwords in case
                        # the database is compromised
                        import uuid
                        hmac_key = uuid.uuid4()
                        line = 'deployment_settings.auth.hmac_key = "%s"' % hmac_key
                    output.write(line)
                output.close()
                input.close()
            else:
                import shutil
                shutil.copy(src_path, dst_path)
            copied_from_template.append(template_files[t])
        else:
            # Found the file in the destination
            # Check if it has been edited
            import re
            edited_pattern = r"FINISHED_EDITING_\w*\s*=\s*(True|False)"
            edited_matcher = re.compile(edited_pattern).match
            has_edited = False
            with open(dst_path) as f:
                for line in f:
                    edited_result = edited_matcher(line)
                    if edited_result:
                        has_edited = True
                        edited = edited_result.group(1)
                        break
            if has_edited and (edited != "True"):
                errors.append("Please edit %s before starting the system." % t)
            # @ToDo: Check if it's up to date (i.e. a critical update requirement)
            #version_pattern = r"VERSION_\w*\s*=\s*([0-9]+)"
            #version_matcher = re.compile(version_pattern).match
            #has_version = False

    if copied_from_template:
        errors.append(
            "The following files were copied from templates and should be edited: %s" %
            ", ".join(copied_from_template))

    return {"error_messages": errors, "warning_messages": warnings}

# =============================================================================
