<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#">

    <!-- **********************************************************************
         RSS Export Templates for Sahana Eden

         Copyright (c) 2010-21 Sahana Software Foundation

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

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Used by base.xsl -->
    <xsl:param name="domain"/>
    <xsl:param name="base_url"/>
    <xsl:param name="title"/>
    <xsl:param name="prefix"/>
    <xsl:param name="name"/>
    <xsl:param name="id"/>
    <xsl:param name="alias"/>
    <xsl:param name="component"/>
    <xsl:param name="mode"/>
    <xsl:param name="utcnow"/>

    <!-- ****************************************************************** -->
    <!-- Defaults if no special case provided here -->
    <xsl:include href="base.xsl"/>
    <xsl:include href="../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Module-specific XSLT -->
    <xsl:include href="modules/cap.xsl"/>
    <xsl:include href="modules/cms.xsl"/>
    <xsl:include href="modules/dvi.xsl"/>
    <xsl:include href="modules/hms.xsl"/>
    <xsl:include href="modules/pr.xsl"/>
    <xsl:include href="modules/project.xsl"/>
    <xsl:include href="modules/req.xsl"/>
    <xsl:include href="modules/supply.xsl"/>

</xsl:stylesheet>
