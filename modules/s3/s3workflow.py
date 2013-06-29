
""" S3 Workflow

    @copyright: 2009-2013 (c) Sahana Software Foundation
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

from s3rest import S3Method
from gluon import *
import uuid
import urllib 
import sys
 
class S3WorkflowNode(object):

    def __init__(self, c, f, m):

        self.c = c
        self.f = f
        self.m = m

    def __call__(self):

        request = current.request
        uid = None
        # look for uuid, if not found assign new one
        if "wf_id" in request.get_vars:
            w = request.get_vars.wf_id.split(":")
            if len(w)>1:
                uid = w[1]
                wf_id = "%s:%s"%(w[0], w[1])
        if uid is None:
            uid = str(uuid.uuid4()) 
            wf_id = "%s:%s"%(w[0], uid)
        return redirect(URL(c = self.c, f = self.f, args= self.m, vars=dict(wf_id = wf_id)))

class S3Workflow(object):

    def __init__(self):

        request = current.request
        session = current.session

        #Get workflow configration and store it in database
        if "wf_id" in request.get_vars:
            w = request.get_vars.wf_id.split(":")
            if len(w) == 1:
                name = w[0]
                module_name = "applications.%s.private.templates.default.workflow" \
                % request.application
                __import__(module_name)
                mymodule = sys.modules[module_name]
                S3WorkflowConfig = mymodule.S3WorkflowConfig()
                config = getattr(S3WorkflowConfig,name)()
                #TODO : store configratoin in the database
                session.v  = config
                session.v  = sorted(session.v.items())

        session.v  = session.v[::-1]
        node = session.v.pop()
        if request.controller == node.c and request.function == node.c and request.args[0] == node.m:
            node = session.v.pop()
        node = node[1]
        #execute the node
        output = node()
