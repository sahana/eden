<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:hxl="http://hxl.humanitarianresponse.info/ns/#"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<!--xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:foaf="http://xmlns.com/foaf/0.1/"
    xmlns:geo="http://www.opengis.net/ont/geosparql#"-->

    <!-- **********************************************************************
         HXL Base Template for Sahana Eden

         Copyright (c) 2013 Sahana Software Foundation

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
    <xsl:template match="/">
        <xsl:apply-templates select="./s3xml"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="s3xml">
        <rdf:RDF xmlns:hxl="http://hxl.humanitarianresponse.info/ns/#"
                 xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
             <!--xmlns:foaf="http://xmlns.com/foaf/0.1/"-->
            <xsl:apply-templates select=".//resource[@name='event_event']" />
            <xsl:apply-templates select=".//resource[@name='org_organisation']" />
            <xsl:apply-templates select=".//resource[@name='project_activity']" />
            <xsl:apply-templates select=".//resource[@name='gis_location']" />
        </rdf:RDF>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="activity_url">
        <xsl:param name="uuid"/>
        <xsl:value-of select="concat($base_url, '/project/activity?~.uuid=', $uuid)"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="event_url">
        <xsl:param name="uuid"/>
        <xsl:value-of select="concat($base_url, '/event/event?~.uuid=', $uuid)"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="location_url">
        <xsl:param name="uuid"/>
        <xsl:value-of select="concat($base_url, '/gis/location?~.uuid=', $uuid)"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="organisation_url">
        <xsl:param name="uuid"/>
        <xsl:value-of select="concat($base_url, '/org/organisation?~.uuid=', $uuid)"/>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
