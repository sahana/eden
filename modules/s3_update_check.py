# -*- coding: utf-8 -*-

import os
import sys

try:
    from gluon import current
except ImportError:
    sys.stderr.write("""
The installed version of Web2py is too old -- it does not define current.
Please upgrade Web2py to a more recent version.
""")
    raise

# Version of 000_config.py
# Increment this if the user should update their running instance
VERSION = 1

#def update_check(environment, template="default"):
def update_check(settings):
    """
        Check whether the dependencies are sufficient to run Eden

        @ToDo: Load deployment_settings so that we can configure the update_check
               - need to rework so that 000_config.py is parsed 1st

        @param settings: the deployment_settings
    """

    # Get Web2py environment into our globals.
    #globals().update(**environment)
    request = current.request

    # Fatal errors
    errors = []
    # Non-fatal warnings
    warnings = []

    # -------------------------------------------------------------------------
    # Check Python libraries

    # Get mandatory global dependencies
    app_path = request.folder

    gr_path = os.path.join(app_path, "requirements.txt")
    or_path = os.path.join(app_path, "optional_requirements.txt")

    global_dep = parse_requirements({}, gr_path)
    optional_dep = parse_requirements({}, or_path)

    templates = settings.get_template()
    if not isinstance(templates, (tuple, list)):
        templates = (templates,)
    template_dep = {}
    template_optional_dep = {}
    for template in templates:
        tr_path = os.path.join(app_path, "modules", "templates", template, "requirements.txt")
        tor_path = os.path.join(app_path, "modules", "templates", template, "optional_requirements.txt")
        parse_requirements(template_dep, tr_path)
        parse_requirements(template_optional_dep, tor_path)

    # Remove optional dependencies which are already accounted for in template dependencies
    unique = set(optional_dep.keys()).difference(set(template_dep.keys()))
    for dependency in optional_dep.keys():
        if dependency not in unique:
            del optional_dep[dependency]

    # Override optional dependency messages from template
    unique = set(optional_dep.keys()).difference(set(template_optional_dep.keys()))
    for dependency in optional_dep.keys():
        if dependency not in unique:
            del optional_dep[dependency]

    errors, warnings = s3_check_python_lib(global_dep, template_dep, template_optional_dep, optional_dep)
    # @ToDo: Move these to Template
    # for now this is done in s3db.climate_first_run()
    if settings.has_module("climate"):
        if settings.get_database_type() != "postgres":
            errors.append("Climate unresolved dependency: PostgreSQL required")
        try:
           import rpy2
        except ImportError:
           errors.append("Climate unresolved dependency: RPy2 required")
        try:
           from Scientific.IO import NetCDF
        except ImportError:
           warnings.append("Climate unresolved dependency: NetCDF required if you want to import readings")
        try:
           from scipy import stats
        except ImportError:
           warnings.append("Climate unresolved dependency: SciPy required if you want to generate graphs on the map")

    # -------------------------------------------------------------------------
    # Check Web2Py version
    #
    # Currently, the minimum usable Web2py is determined by whether the
    # Scheduler is available
    web2py_minimum_version = "Version 2.4.7-stable+timestamp.2013.05.27.11.49.44"
    # Offset of datetime in return value of parse_version.
    datetime_index = 4
    web2py_version_ok = True
    try:
        from gluon.fileutils import parse_version
    except ImportError:
        web2py_version_ok = False
    if web2py_version_ok:
        try:
            web2py_minimum_parsed = parse_version(web2py_minimum_version)
            web2py_minimum_datetime = web2py_minimum_parsed[datetime_index]
            version_info = open("VERSION", "r")
            web2py_installed_version = version_info.read().split()[-1].strip()
            version_info.close()
            if isinstance(web2py_installed_version, str):
                # Post 2.4.2, global_settings.web2py_version is unparsed
                web2py_installed_parsed = parse_version(web2py_installed_version)
                web2py_installed_datetime = web2py_installed_parsed[datetime_index]
            else:
                # 2.4.2 & earlier style
                web2py_installed_datetime = web2py_installed_version[datetime_index]
            web2py_version_ok = web2py_installed_datetime >= web2py_minimum_datetime
        except:
            # Will get AttributeError if Web2py's parse_version is too old for
            # its current version format, which changed in 2.3.2.
            web2py_version_ok = False
    if not web2py_version_ok:
        warnings.append(
            "The installed version of Web2py is too old to support the current version of Sahana Eden."
            "\nPlease upgrade Web2py to at least version: %s" % \
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
    # - 000_config.py (machine-specific settings)
    # - rest are run in-place
    #
    template_folder = os.path.join(app_path, "modules", "templates")

    template_files = {
        # source : destination
        "000_config.py" : os.path.join("models", "000_config.py"),
    }

    copied_from_template = []

    for t in template_files:
        src_path = os.path.join(template_folder, t)
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
                        line = 'settings.auth.hmac_key = "%s"' % hmac_key
                    output.write(line)
                output.close()
                input.close()
            else:
                import shutil
                shutil.copy(src_path, dst_path)
            copied_from_template.append(template_files[t])

            # @ToDo: WebSetup
            #  http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/WebSetup
            #if not os.path.exists("%s/applications/websetup" % os.getcwd()):
            #    # @ToDo: Check Permissions
            #    # Copy files into this folder (@ToDo: Pythonise)
            #    cp -r private/websetup "%s/applications" % os.getcwd()
            # Launch WebSetup
            #redirect(URL(a="websetup", c="default", f="index",
            #             vars=dict(appname=request.application,
            #                       firstTime="True")))
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
            # Check if it's up to date (i.e. a critical update requirement)
            version_pattern = r"VERSION =\s*([0-9]+)"
            version_matcher = re.compile(version_pattern).match
            has_version = False
            with open(dst_path) as f:
                for line in f:
                    version_result = version_matcher(line)
                    if version_result:
                        has_version = True
                        version = version_result.group(1)
                        break
            if not has_version:
                error = "Your %s is using settings from the old templates system. Please switch to the new templates system: http://eden.sahanafoundation.org/wiki/DeveloperGuidelines/Templates" % t
                errors.append(error)
            elif int(version) != VERSION:
                error = "Your %s is using settings from template version %s. Please update with new settings from template version %s before starting the system." % \
                                (t, version, VERSION)
                errors.append(error)

    if copied_from_template:
        errors.append(
            "The following files were copied from templates and should be edited: %s" %
            ", ".join(copied_from_template))

    return {"error_messages": errors, "warning_messages": warnings}

# -------------------------------------------------------------------------
def parse_requirements(output, filepath):
    """
    """

    try:
        with open(filepath) as filehandle:
            dependencies = filehandle.read().splitlines()
            msg = ""
            for dependency in dependencies:
                if dependency[0] == "#":
                    # either a normal comment or custom message
                    if dependency[:9] == "# Warning" or dependency[7] == "# Error:":
                        msg = dependency.split(":", 1)[1]
                else:
                    import re
                    # Check if the module name is different from the package name
                    if "#" in dependency:
                        dep = dependency.split("#", 1)[1]
                        output[dep] = msg
                    else:
                        pattern = re.compile(r'([A-Za-z0-9_-]+)')
                        try:
                            dep = pattern.match(dependency).group(1)
                            output[dep] = msg
                        except AttributeError:
                            # Invalid dependency syntax
                            pass
                    msg = ""
    except IOError:
        # No override for Template
        pass

    return output

# -------------------------------------------------------------------------
def s3_check_python_lib(global_mandatory, template_mandatory, template_optional, global_optional):
    """
        checks for optional as well as mandatory python libraries
    """

    errors = []
    warnings = []

    for dependency, err in global_mandatory.iteritems():
        try:
            if "from" in dependency:
                exec dependency
            else:
                exec "import %s" % dependency
        except ImportError:
            if err:
                errors.append(err)
            else:
                errors.append("S3 unresolved dependency: %s required for Sahana to run" % dependency)

    for dependency, err in template_mandatory.iteritems():
        try:
            if "from" in dependency:
                exec dependency
            else:
                exec "import %s" % dependency
        except ImportError:
            if err:
                errors.append(err)
            else:
                errors.append("Unresolved template dependency: %s required" % dependency)

    for dependency, warn in template_optional.iteritems():
        try:
            if "from" in dependency:
                exec dependency
            else:
                exec "import %s" % dependency
        except ImportError:
            if warn:
                warnings.append(warn)
            else:
                warnings.append("Unresolved optional dependency: %s required" % dependency)

    for dependency, warn in global_optional.iteritems():
        try:
            if "from" in dependency:
                exec dependency
            else:
                exec "import %s" % dependency
        except ImportError:
            if warn:
                warnings.append(warn)
            else:
                warnings.append("Unresolved optional dependency: %s required" % dependency)

    return errors, warnings

# END =========================================================================
