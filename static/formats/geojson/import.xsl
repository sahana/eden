<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************

         GeoJSON Import Templates for Sahana-Eden

         http://geojson.org/geojson-spec.html

         Version 0.2 / 2010-12-02

         Copyright (c) 2010-12 Sahana Software Foundation

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
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./geojson"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="geojson">
        <xsl:choose>
            <xsl:when test="./features">
                <xsl:for-each select="./features">
                    <xsl:call-template name="location"/>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="location"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- ****************************************************************** -->
    <xsl:template name="location">

        <xsl:variable name="ID" select="./properties/id/text()"/>
        <xsl:variable name="Name" select="./properties/name/text()"/>

        <resource name="gis_location">

            <xsl:if test="$ID!=''">
                <xsl:attribute name="uuid"><xsl:value-of select="$ID"/></xsl:attribute>
            </xsl:if>

            <xsl:if test="$Name!=''">
                <data field="name"><xsl:value-of select="$Name"/></data>
            </xsl:if>

            <xsl:choose>

                <xsl:when test="./geometry/type/text()='Point'">
                    <data field="gis_feature_type">1</data>
                    <data field="lon">
                        <xsl:value-of select="./geometry/coordinates[1]/text()"/>
                    </data>
                    <data field="lat">
                        <xsl:value-of select="./geometry/coordinates[2]/text()"/>
                    </data>
                </xsl:when>

                <!-- @ToDo: Handle Polygons
                <xsl:when test="./geometry/type/text()='Polygon'">
                    <data field="gis_feature_type">3</data>
                    <data field="wkt">
                        <xsl:text>POLYGON((</xsl:text>
                        <!- @ToDo Loop through Coordinates to build WKT string
                        <xsl:value-of select="./geometry/coordinates[1]/text()"/>
                        <xsl:value-of select="./geometry/coordinates[2]/text()"/>
                        <xsl:text>))</xsl:text>
                    </data>
                </xsl:when>
                -->

            </xsl:choose>

            <!-- @ToDo: Support CRS -->

        </resource>
    </xsl:template>

</xsl:stylesheet>