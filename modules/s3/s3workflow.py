
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


class S3WorkflowExitNode(object):
    """
        The S3 Worfklow Exit Node class
    """
    def __call__(self,request):
        """
            Executes the Exit Node
            @param request: The S3 Reuqest 
        """

        request.vars.wf_id = None
        redirect(URL(c = "default",
                     f = "index"))        

# ==========================================================================

class S3Workflow(object):
    """
        Class to Execute the workflow
    """

    def __init__(self, left = None, op = None, right = None):
        """
            Workflow Constructor
        """

        self.left = left
        self.op = op 
        self.right = right

    # ----------------------------------------------------------------------
    def node(self,c,f,m)
        """
            Node Constuctor
            @param c: controller
            @param f: function
            @param m: method 
        """

        self.c = c
        self.f = f
        self.m = m
        
        return a(self)
    # ----------------------------------------------------------------------
    def __and__(self, other):
        """ AND """

        return S3Workflow(self, "and", other)
   
    # ----------------------------------------------------------------------
    def __or__(self, other):
        """ OR """

        return S3Workflow(self, "or", other)

    # ----------------------------------------------------------------------
    def __call__(self,request):
        """
            Excutes the Node 
            @param request: The S3 Request
        """

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

        return redirect(URL(c = self.c,
                            f = self.f,
                            args = self.m,
                            vars = dict(wf_id = wf_id)))

    # ----------------------------------------------------------------------
    def execute(self,request):
        """
            Reads the workflow configration and executes the workflow
            @param request: The S3 Request 
        """

        #Get workflow configration and store it in database
        if "wf_id" in request.get_vars:
            w = request.get_vars.wf_id.split(":")
            if len(w) == 1:
                name = w[0]
                module_name = "applications.%s.private.templates.default.workflow" \
                % request.application
                try: 
                    __import__(module_name)
                except ImportError:
                    return
                mymodule = sys.modules[module_name]
                S3WorkflowConfig = mymodule.S3WorkflowConfig()
                if hasattr(S3WorkflowConfig, name):
                    workflow = getattr(S3WorkflowConfig,name)()
                else:
                    raise SyntaxError, "Invalid Workflow Name: %s" % name 

        #execute the node
        node = workflow.right.right.left 
        output = node(request)

    # -----------------------------------------------------------------------
    def __repr__(self):
        
        r = ""
        def addnode(self, r):

            if self.l and self.r:
                if self.op is "and":
                    op = "& "
                    r = gn(self.l,r)
                    r = r + "%s"%op
                    r = gn(self.r,r)
                elif self.op is "or":
                    op = "| "
                    r += "( " 
                    r = addnode(self.l, r)
                    r = r + '%s'%op
                    r = addnode(self.r, r)
                    r += ") " 
            elif slef.l:
                if self.c:
                    r = r + "%s(%s) "%(self.__class__.__name__, self.l.c)
        r = addnode(self,r)
        rep = "<%s { %s }>"%(self.__class__.__name__,r) 
        return rep

# END ======================================================================
