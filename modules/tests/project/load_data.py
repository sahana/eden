""" Sahana Eden Module Automated Tests - Load Data

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

import os
try:
    from cStringIO import StringIO    # Faster, where available
except:
    from StringIO import StringIO

from lxml import etree

from gluon import current
from gluon.storage import Storage

#def load_data():
db = current.db
s3db = current.s3db
auth = current.auth
request = current.request

#----------------------------------------------------------------------
# Initialize Data & Users
auth.override = True
s3db.load_all_models()

test_dir = os.path.join(current.request.folder, "modules",
                        "tests", "project")

task_file = open(os.path.join(test_dir, "project_task.csv"), "rb")
time_file = open(os.path.join(test_dir, "project_time.csv"), "rb")

task_stylesheet = os.path.join(current.request.folder, "static", "formats", "s3csv", "project", "task.xsl")
time_stylesheet = os.path.join(current.request.folder, "static", "formats", "s3csv", "project", "time.xsl")

#project_data = open(os.path.join(test_dir, "project_time.xml"), "rb")
#project_data = open(os.path.join("/code", "sandbox", "time.xml"), "rb")

project_resource = s3db.resource("project_project")
task_resource = s3db.resource("project_task")
time_resource = s3db.resource("project_time")

#task_resource.import_xml(task_file, format="csv", stylesheet=task_stylesheet)
time_resource.import_xml(time_file, format="csv", stylesheet=time_stylesheet)

#xmltree = etree.ElementTree( etree.fromstring(project_data.read()) )
#success = time_resource.import_xml(xmltree)

db.commit()