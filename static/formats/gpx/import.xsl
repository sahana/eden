<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:gpx="http://www.topografix.com/GPX/1/0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************

         GPX Import Templates for S3XRC

         Copyright (c) 2010 Sahana Software Foundation

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
    -->

    <!-- ****************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Root element -->
    <xsl:template match="/">
        <xsl:apply-templates select="gpx:gpx"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="gpx:gpx">
        <s3xml>
            <!-- Waypoints -->
            <xsl:apply-templates select="gpx:wpt"/>
            <!-- Tracks -->
            <!--
            <xsl:apply-templates select="trk"/>
            -->
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="gpx:wpt">
        <resource name="gis_waypoint">
            <!-- wrong format
            <xsl:attribute name="created_on">
                <xsl:call-template name="iso2datetime">
                    'cmt' & 'desc' have this info, but which is best to use? 'time' element would be better but not in my samples
                    <xsl:with-param name="datetime" select="./cmt/text()"/>
                </xsl:call-template>
            </xsl:attribute>
            -->

            <data field="name">
                <xsl:value-of select="./gpx:name/text()"/>
            </data>

            <!-- Do a lookup on symbol? How likely is it to be populated sensibly in practise?
            <data field="category">
                <xsl:value-of select="./sym/text()"/>
            </data>
            -->

            <reference field="location_id" resource="gis_location">
                <xsl:call-template name="location"/>
            </reference>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="gpx:trk">
        <!-- @ToDo -->
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="location">
        <resource name="gis_location">
            <data field="name">
                <xsl:value-of select="./gpx:name/text()"/>
            </data>
            <data field="gis_feature_type" value="1">Point</data>
            <data field="lat">
                <xsl:value-of select="@gpx:lat"/>
            </data>
            <data field="lon">
                <xsl:value-of select="@gpx:lon"/>
            </data>
            <data field="elevation">
                <xsl:value-of select="./gpx:ele/text()"/>
            </data>
        </resource>
    </xsl:template>

</xsl:stylesheet>