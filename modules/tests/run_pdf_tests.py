#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Needs to be run in the web2py environment
# python web2py.py -S eden -M -R applications/clean/modules/tests/run_pdf_tests.py

import os
from gluon import *
from gluon.storage import Storage
from s3.s3rest import S3Request
from gluon.contrib.pdfinvoice import PDF

WRITE_PDF = True

def header(r):
    img_path = os.path.join(current.request.application,
                        "static", "img","sahanalarge_14.png")
    html_h = TABLE(TR(TD(IMG(_src=os.path.sep+img_path)),
                      TD("A lovely Title"),
                      TD(DIV(P("Right aligned text"),P("<i>not yet implemented</i>")),_align="right")),
                     TR(TD("This is a test header. These details should be" +
                         " displayed on every page. This dull and meaningless" +
                         " text should stretch across the entire page," +
                         " and then wrap around onto a second line.",_colspan=3)
                      )
                   )
    return DIV(html_h)
def footer(r):
    return P("A footer that will appear at the end of each page.", _halign="center")
def body_1(r):
    # Here is some hard-coded test data
    name = "Mr. Administrator, Sir"
    org_name = "Example"
    email = "admin@example.com"
    logo_path = os.path.join(current.request.application,
                        "static", "img","blank-user.gif")
    innerTable = TABLE(TR(TH(T("Name")), TH(T("Organisation")), TH(T("Email"))),
                       TR(TD(TD(name),TD(org_name),TD(email)))
                       )
    person_details = TABLE(TR(TD(IMG(_src=os.path.sep+logo_path)),
                              TD(innerTable)
                              ))

    todo = DIV(P("So here is a list of features that could be added."),
               LI("Extend basic html tag support: H1, H2, etc, LI, etc"),
               LI("Add support for standard attributes: align, halign, valign"),
               LI("Make the header and footer fit on a landscape page if the table changes the page layout"),
               LI("Be able to control the width of table cells, being more smart about this would be good, but probably harder to implement. See the above tables the cells in the heading are all the same width. The inner table overflows the outer table."),
               )
    

    # Now put all the output together
    output = DIV(H1("<b><h1>Here is an example of hardcoded data, created via a callback function which returns html.</h1></b>"),
                 P("<i>Unfortunately, the header tags don't yet work these can be added in the s3codecs/pdf.py file</i>"),
                 TABLE(TR(TH(T("Volunteer Service Record")))),
                 person_details,
                 todo,
                 )

    return output

def test_pdf1():
    """
        Generate a Test PDF that will demonstrate S3RL_PDF functionality
    """
    r = S3Request(prefix="pr", name="person")
    T = current.T
    from s3.s3export import S3Exporter
    exporter = S3Exporter().pdf
    return exporter(r.resource,
                    request = r,
                    method = "list",
                    pdf_title = T("PDF Test Card I"),
                    pdf_header = header,
                    pdf_callback = body_1,
                    pdf_footer = footer
                    )

def test_pdf2():
    """
        Generate a Test PDF that will demonstrate S3RL_PDF functionality
    """
    r = S3Request(prefix="gis", name="hierarchy")
    from s3.s3export import S3Exporter
    exporter = S3Exporter().pdf
    return exporter(r.resource,
                    request = r,
                    method = "list",
                    pdf_title = T("PDF Test Card II"),
                    pdf_table_autogrow = "B",
                    pdf_header = header,
                    pdf_footer = footer
                    )

pdf = test_pdf1()

if WRITE_PDF:
    filename = os.path.join("applications", current.request.application,
                        "modules", "tests", "test_pdf_1.pdf")
    f = open(filename, 'wb')
    f.write(pdf)
    f.close()

pdf = test_pdf2()

if WRITE_PDF:
    filename = os.path.join("applications", current.request.application,
                        "modules", "tests", "test_pdf_2.pdf")
    f = open(filename, 'wb')
    f.write(pdf)
    f.close()

