# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

"""
   This file imports the Message parsers from the core code
   and links them with the respective parsing tasks defined in msg_workflow.

   @author: Ashwyn Sharma <ashwyn1092[at]gmail.com>
   @copyright: 2012 (c) Sahana Software Foundation
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

from gluon import current

class S3Parsing(object):
    """
       Message Parsing Framework.
    """

    # ---------------------------------------------------------------------
    @staticmethod
    def parser(workflow, message = ""):
        """
           Parsing Workflow Filter.
           Called by parse_import() in s3msg.py.
        """
        settings = current.deployment_settings
        import sys
        parser = settings.get_msg_parser()
        application = current.request.application
        module_name = 'applications.%s.private.templates.%s.parser' \
            %(application, parser)
        __import__(module_name)
        mymodule = sys.modules[module_name]
        S3Parsing = mymodule.S3Parsing()
        
        import inspect
        parsers = inspect.getmembers(S3Parsing, predicate=inspect.isfunction)
        parse_opts = []
        for parser in parsers:
            parse_opts += [parser[0]]

        for parser in parse_opts:
            if parser == workflow:
                result = getattr(S3Parsing, parser)
                return result(message)

# END =========================================================================
