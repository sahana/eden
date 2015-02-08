<xsl:stylesheet version="1.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns="http://www.topografix.com/GPX/1/1"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- **********************************************************************

         GPX Export Template for S3XRC

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

    *********************************************************************** -->
    <xsl:output method="xml" indent="yes"/>

    <!-- ****************************************************************** -->
    <xsl:param name="domain"/>
    <xsl:param name="base_url"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <xsl:apply-templates select="s3xml"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="/s3xml">
        <gpx xsi:schemaLocation="http://www.topografix.com/GPX/1/1
            http://www.topografix.com/GPX/1/1/gpx.xsd"
            version="1.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xmlns="http://www.topografix.com/GPX/1/1">
            <xsl:attribute name="creator"><!-- <xsl:value-of select="$domain"/> -->Sahana Eden</xsl:attribute>
            <bounds>
                <xsl:attribute name="minlat"><xsl:value-of select="@latmin"/></xsl:attribute>
                <xsl:attribute name="minlon"><xsl:value-of select="@lonmin"/></xsl:attribute>
                <xsl:attribute name="maxlat"><xsl:value-of select="@latmax"/></xsl:attribute>
                <xsl:attribute name="maxlon"><xsl:value-of select="@lonmax"/></xsl:attribute>
            </bounds>
            <xsl:apply-templates select=".//resource[@name='gis_location']"/>
        </gpx>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_location']">
        <xsl:variable name="uid">
            <xsl:value-of select="@uuid"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="//reference[@resource='gis_location' and @uuid=$uid]">
                <xsl:for-each select="//reference[@resource='gis_location' and @uuid=$uid]">
                    <xsl:apply-templates select=".."/>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <wpt>
                    <xsl:attribute name="lat"><xsl:value-of select="data[@field='lat']"/></xsl:attribute>
                    <xsl:attribute name="lon"><xsl:value-of select="data[@field='lon']"/></xsl:attribute>
                    <name><xsl:value-of select="data[@field='name']"/></name>
                    <desc><xsl:value-of select="@url"/></desc>
                    <sym><xsl:value-of select="@sym"/></sym>
                </wpt>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='hms_hospital']">
        <xsl:if test="reference[@field='location_id']">
            <wpt>
                <xsl:attribute name="lat"><xsl:value-of select="reference[@field='location_id']/@lat"/></xsl:attribute>
                <xsl:attribute name="lon"><xsl:value-of select="reference[@field='location_id']/@lon"/></xsl:attribute>
                <name><xsl:value-of select="data[@field='name']"/></name>
                <desc>
                    <xsl:if test="reference[@field='organisation_id']/text()">
                        <xsl:value-of select="reference[@field='organisation_id']"/>
                        <xsl:text> </xsl:text>
                    </xsl:if>
                    <xsl:value-of select="data[@field='facility_type']"/>
                </desc>
                <sym><xsl:value-of select="reference[@field='location_id']/@sym"/></sym>
            </wpt>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource">
        <xsl:if test="reference[@field='location_id']">
            <wpt>
                <xsl:attribute name="lat"><xsl:value-of select="reference[@field='location_id']/@lat"/></xsl:attribute>
                <xsl:attribute name="lon"><xsl:value-of select="reference[@field='location_id']/@lon"/></xsl:attribute>
                <name><xsl:value-of select="data[@field='name']"/></name>
                <desc>
                    <xsl:if test="reference[@field='organisation_id']/text()">
                        <xsl:value-of select="reference[@field='organisation_id']"/>
                        <xsl:text> </xsl:text>
                    </xsl:if>
                    <xsl:value-of select="data[@field='type']"/>
                </desc>
                <sym><xsl:value-of select="reference[@field='location_id']/@sym"/></sym>
            </wpt>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>
