"""
    Update Check

    Copyright: 2024 (c) Sahana Software Foundation

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

import os
import re
import sys

from gluon import current
from gluon.fileutils import parse_version

class UpdateCheck:

    # This is the current version of requirements
    REQUIREMENTS = 5

    # This is the required version of models/000_config.py
    CONFIG = 1

    # -------------------------------------------------------------------------
    @classmethod
    def check_all(cls):
        """
            Performs all update checks:
                - Python library dependencies
                - web2py version
                - configuration files

            Returns:
                tuple of lists of strings (errors, warnings)
        """

        errors, warnings = [], []

        # Check Python libraries
        e, w = cls.check_python_libs()
        errors.extend(e)
        warnings.extend(w)

        # Check Web2Py version
        e, w = cls.check_web2py_version()
        errors.extend(e)
        warnings.extend(w)

        # Check config files
        e, w = cls.check_config()
        errors.extend(e)
        warnings.extend(w)

        # Create required directories if needed
        databases_dir = os.path.join(current.request.folder, "databases")
        try:
            os.stat(databases_dir)
        except OSError:
            # not found, create it
            os.mkdir(databases_dir)

        return errors, warnings

    # -------------------------------------------------------------------------
    @staticmethod
    def check_web2py_version():
        """
            Checks the web2py version for compatibility

            Returns:
                tuple of lists of strings (errors, warnings)
        """

        # We require web2py-2.21.1 or later for PyDAL compatibility
        web2py_minimum_version = "Version 2.21.2-stable+timestamp.2021.10.15.07.44.23"

        version_ok = True
        try:
            required = parse_version(web2py_minimum_version)[4]

            try:
                with open("VERSION", "r") as version:
                    web2py_installed_version = version.read().split()[-1].strip()
                installed = parse_version(web2py_installed_version)[4]
                version_ok = installed >= required
            except IOError:
                # VERSION file not found (e.g. git clone or docker), assume OK or warn
                # For now, we assume OK to avoid blocking deployment
                version_ok = True
        except AttributeError:
            version_ok = False

        if not version_ok:
            msg = "\n".join(("The installed version of Web2py is too old to support the current version of Eden.",
                             "Please upgrade Web2py to at least version: %s" % web2py_minimum_version,
                             ))
            errors = [msg]
        else:
            errors = []

        return errors, []

    # -------------------------------------------------------------------------
    @classmethod
    def check_python_libs(cls):
        """
            Checks for python libraries Eden depends on, both mandatory
            and optional dependencies

            Returns:
                tuple of lists of strings (errors, warnings)
        """

        folder = current.request.folder

        mandatory = cls.parse_requirements({}, os.path.join(folder, "requirements.txt"))
        optional = cls.parse_requirements({}, os.path.join(folder, "optional_requirements.txt"))

        pyversion = sys.version_info[:2]
        if pyversion[0] < 3 or pyversion[1] < 9:
            remove_prefix = lambda d: d[7:] if d.startswith("python-") else d
        else:
            remove_prefix = lambda d: d.removeprefix("python-")

        errors, warnings = [], []

        checks = ((mandatory, errors, "Unresolved dependency: %s required"),
                  (optional, warnings, "Unresolved optional dependency: %s required"),
                  )

        for dependencies, messages, template in checks:
            for dependency, error in dependencies.items():
                try:
                    if "from" in dependency:
                        exec(dependency)
                    else:
                        __import__(remove_prefix(dependency))
                except ImportError:
                    if error:
                        messages.append(error)
                    else:
                        messages.append(template % dependency)
                except Exception:
                    # Broken module
                    messages.append("Error when loading optional dependency: %s" % dependency)

        return errors, warnings

    # -------------------------------------------------------------------------
    @classmethod
    def check_config(cls):
        """
            Checks 000_config.py

            Returns:
                tuple of lists of strings (errors, warnings)
        """

        dst = ("models", "000_config.py")
        src = ("modules", "templates", "000_config.py")

        errors = []

        folder = current.request.folder
        path = os.path.join(*dst)

        dst_path = os.path.join(folder, path)
        src_path = os.path.join(folder, *src)
        try:
            os.stat(dst_path)
        except OSError:
            cls.copy_config_from_template(src_path, dst_path)

        # Check if it has been edited
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
        if has_edited and edited != "True":
            error = "Please edit %s before starting the system." % path
            errors.append(error)

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
        if not has_version or int(version) != cls.CONFIG:
            error = "Your %s is incompatible with the current version of Eden. Please update with new settings from template %s" % \
                    (path, os.path.join(*src))
            errors.append(error)

        return errors, []

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_requirements(output, path):
        """
            Parses a requirements.txt file

            Args:
                output: the output dict to store the requirements {dependency: message}
                path: the file path of the requirements file

            Returns:
                the output dict
        """

        try:
            with open(path) as f:
                dependencies = f.read().splitlines()
                msg = ""
                for dependency in dependencies:
                    if dependency[0] == "#":
                        # Either a normal comment or custom message
                        if dependency[:9] == "# Warning" or dependency[7] == "# Error:":
                            msg = dependency.split(":", 1)[1]
                    else:
                        # Check if the module name is different from the package name
                        if "#" in dependency:
                            dep = dependency.split("#", 1)[1].strip()
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
            # No requirements file
            pass

        return output

    # -------------------------------------------------------------------------
    @staticmethod
    def copy_config_from_template(src_path, dst_path):
        """
            Copies 000_config.py from its template

            Args:
                src_path: the source path (i.e. the template)
                dst_path: the destination path
        """

        with open(src_path) as src:
            with open(dst_path, "w") as dst:
                for line in src:
                    if "akeytochange" in line:
                        # Generate a random hmac_key to secure the passwords in case
                        # the database is compromised
                        import uuid
                        hmac_key = uuid.uuid4()
                        line = 'settings.auth.hmac_key = "%s"' % hmac_key
                    dst.write(line)

# END =========================================================================
