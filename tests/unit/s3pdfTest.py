import os
import sys
import StringIO

path = "../../../../"
sys.path = [path]+[p for p in sys.path if not p==path]
sys.path.append("../../modules/s3")

from s3pdf import S3PDF, S3PDFORCForm

def route1():
    filename = "testOCRFORM_R1.pdf"
    output = StringIO.StringIO()
    doc = S3PDFORCForm(filename, output, 40, 40, 50, 50)
    doc.build()

def route2():
    filename = "testOCRFORM_R2.pdf"
    pdf = S3PDF()
    doc = pdf.newOCRForm(filename)
    pdf.doc.build()

route1()
route2()