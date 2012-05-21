<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:georss="http://www.georss.org/georss"
    xmlns:gdacs="http://www.gdacs.org"
    xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         GeoRSS Import Templates for Sahana-Eden

         Copyright (c) 2011-2012 Sahana Software Foundation

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
    <xsl:output method="xml" indent="yes"/>
    <xsl:include href="../xml/commons.xsl"/>

    <!-- Which Resource? -->
    <xsl:param name="name"/>
    <!-- Source URL for Feed caching -->
    <xsl:param name="source_url"/>
    <!-- Data element for Feed caching -->
    <xsl:param name="data_field"/>
    <!-- Image element for Feed caching -->
    <xsl:param name="image_field"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:for-each select="//item">
                <xsl:choose>
                    <!-- Cache -->
                    <xsl:when test="$name='cache'">
                        <xsl:call-template name="cache"/>
                    </xsl:when>

                    <!-- GDACS -->
                    <xsl:when test="$name='gdacs'">
                        <xsl:call-template name="gdacs"/>
                    </xsl:when>

                    <!-- Default to Locations -->
                    <xsl:otherwise>
                        <resource name="gis_location">
                            <xsl:call-template name="location"/>
                        </resource>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="cache">
        <resource name="gis_cache">

            <xsl:attribute name="uuid">
                <xsl:value-of select="concat($source_url, '/', ./guid/text())"/>
            </xsl:attribute>

            <data field="title">
                <xsl:value-of select="./title/text()"/>
            </data>
            <data field="description">
                <xsl:value-of select="./description/text()"/>
            </data>
            <data field="link">
                <xsl:value-of select="./link/text()"/>
            </data>

            <!-- Handle Points -->
            <xsl:call-template name="point"/>

            <data field="data">
                <!-- @ToDo: Right-trim too -->
                <xsl:call-template name="left-trim">
                    <xsl:with-param name="s" select="./*[name()=$data_field]/text()"/>
                </xsl:call-template>
            </data>
            <data field="image">
                <!-- @ToDo: Right-trim too -->
                <xsl:call-template name="left-trim">
                    <xsl:with-param name="s" select="./*[name()=$image_field]/text()"/>
                </xsl:call-template>
            </data>
            <data field="source">
                <xsl:value-of select="$source_url"/>
            </data>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="gdacs">
        <resource name="alert_gdacs">

            <xsl:attribute name="uuid">
                <xsl:value-of select="concat('gdacs:', ./gdacs:eventid/text())"/>
            </xsl:attribute>

            <data field="name">
                <xsl:value-of select="./title/text()"/>
            </data>
            <data field="description">
                <xsl:value-of select="./description/text()"/>
            </data>
            <data field="link">
                <xsl:value-of select="./link/text()"/>
            </data>

            <data field="date_start">
                <xsl:value-of select="./gdacs:fromdate/text()"/>
            </data>
            <data field="date_end">
                <xsl:value-of select="./gdacs:todate/text()"/>
            </data>
            <data field="type">
                <xsl:value-of select="./gdacs:eventtype/text()"/>
            </data>
            <data field="level">
                <xsl:value-of select="./gdacs:alertlevel/text()"/>
            </data>

            <!-- Location Info -->
            <reference field="location_id" resource="gis_location">
                <xsl:call-template name="location"/>
            </reference>

        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="location">
        <data field="name">
            <xsl:value-of select="./title/text()"/>
        </data>

        <xsl:if test="$name='cache'">
            <data field="comments">
                <xsl:value-of select="./description/text()"/>
            </data>
        </xsl:if>

        <!-- Handle Points -->
        <data field="gis_feature_type">1</data>
        <xsl:call-template name="point"/>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="point">
        <xsl:choose>
            <xsl:when test="./georss:point/text() != ''">
                <data field="lat">
                    <xsl:call-template name="lat">
                        <xsl:with-param name="latlon" select="./georss:point/text()"/>
                    </xsl:call-template>
                </data>
                <data field="lon">
                    <xsl:call-template name="lon">
                        <xsl:with-param name="latlon" select="./georss:point/text()"/>
                    </xsl:call-template>
                </data>
            </xsl:when>
            <xsl:otherwise>
                <data field="lat">
                    <xsl:value-of select=".//geo:lat/text()"/>
                </data>
                <data field="lon">
                    <xsl:value-of select=".//geo:long/text()"/>
                </data>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="lat">
        <xsl:param name="latlon"/>
        <xsl:call-template name="left-trim">
            <xsl:with-param name="s" select="substring-before($latlon, ' ')"/>
        </xsl:call-template>
    </xsl:template>

    <xsl:template name="lon">
        <xsl:param name="latlon"/>
        <xsl:call-template name="right-trim">
            <xsl:with-param name="s" select="substring-after($latlon, ' ')"/>
        </xsl:call-template>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
