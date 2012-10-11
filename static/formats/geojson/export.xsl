<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************

         GeoJSON Export Templates for Sahana-Eden

         Copyright (c) 2012 Sahana Software Foundation

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

    <xsl:param name="prefix"/>
    <xsl:param name="name"/>

    <xsl:template match="/">
        <GeoJSON>
            <xsl:apply-templates select="s3xml"/>
        </GeoJSON>
    </xsl:template>

    <xsl:template match="s3xml">
        <xsl:variable name="results">
            <xsl:value-of select="@results"/>
        </xsl:variable>
        <xsl:if test="$results &gt; 0">
            <xsl:variable name="resource">
                <xsl:value-of select="concat($prefix, '_', $name)"/>
            </xsl:variable>
            <xsl:choose>
                <!-- skip if all resources have no latlon defined
                <xsl:when test="not(//reference[@name='location'])">
                </xsl:when> -->
                <xsl:when test="count(./resource[@name=$resource])=1">
                    <xsl:apply-templates select="./resource[@name=$resource]"/>
                </xsl:when>
                <xsl:otherwise>
                    <type>FeatureCollection</type>
                    <xsl:for-each select="./resource[@name=$resource]">
                        <features>
                            <xsl:apply-templates select="."/>
                        </features>
                    </xsl:for-each>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_location']">
        <xsl:variable name="uid" select="./@uuid"/>
        <xsl:choose>
            <xsl:when test="//reference[@resource='gis_location' and @uuid=$uid]">
                <xsl:for-each select="//reference[@resource='gis_location' and @uuid=$uid]">
                    <xsl:if test="not(../@name='gis_location')">
                        <xsl:apply-templates select=".."/>
                    </xsl:if>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <type>Feature</type>
                <geometry>
                    <type>
                        <xsl:text>Point</xsl:text>
                    </type>
                    <coordinates>
                        <xsl:value-of select="data[@field='lon']"/>
                    </coordinates>
                    <coordinates>
                        <xsl:value-of select="data[@field='lat']"/>
                    </coordinates>
                </geometry>
                <properties>
                    <id>
                        <xsl:value-of select="$uid"/>
                    </id>
                    <name>
                        <xsl:value-of select="data[@field='name']"/>
                    </name>
                    <marker>
                        <xsl:value-of select="@marker"/>
                    </marker>
                    <popup>
                        <xsl:value-of select="@popup"/>
                    </popup>
                    <url>
                        <xsl:value-of select="@url"/>
                    </url>
                </properties>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_cache']">
        <!-- GeoRSS or KML -->
        <type>Feature</type>
        <geometry>
            <type>
                <xsl:text>Point</xsl:text>
            </type>
            <coordinates>
                <xsl:value-of select="data[@field='lon']"/>
            </coordinates>
            <coordinates>
                <xsl:value-of select="data[@field='lat']"/>
            </coordinates>
        </geometry>
        <properties>
            <name>
                <xsl:value-of select="data[@field='title']"/>
            </name>
            <description>
                <xsl:value-of select="data[@field='description']"/>
            </description>
            <!-- Used by GeoRSS -->
            <link>
                <xsl:value-of select="data[@field='link']"/>
            </link>
            <data>
                <xsl:value-of select="data[@field='data']"/>
            </data>
            <image>
                <xsl:value-of select="data[@field='image']"/>
            </image>
            <!-- Used by KML -->
            <marker>
                <xsl:value-of select="data[@field='marker']"/>
            </marker>
        </properties>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_feature_query']">
        <!-- Feature Query -->
        <type>Feature</type>
        <geometry>
            <type>
                <xsl:text>Point</xsl:text>
            </type>
            <coordinates>
                <xsl:value-of select="data[@field='lon']"/>
            </coordinates>
            <coordinates>
                <xsl:value-of select="data[@field='lat']"/>
            </coordinates>
        </geometry>
        <properties>
            <popup>
                <xsl:value-of select="data[@field='popup_label']"/>
            </popup>
            <url>
                <xsl:value-of select="data[@field='popup_url']"/>
            </url>
            <xsl:choose>
                <xsl:when test="data[@field='marker_url']">
                    <marker_url>
                        <xsl:value-of select="data[@field='marker_url']"/>
                    </marker_url>
                    <marker_height>
                        <xsl:value-of select="data[@field='marker_height']"/>
                    </marker_height>
                    <marker_width>
                        <xsl:value-of select="data[@field='marker_width']"/>
                    </marker_width>
                </xsl:when>
                <xsl:otherwise>
                    <shape>
                        <xsl:value-of select="data[@field='shape']"/>
                    </shape>
                    <size>
                        <xsl:value-of select="data[@field='size']"/>
                    </size>
                    <colour>
                        <xsl:value-of select="data[@field='colour']"/>
                    </colour>
                    <xsl:if test="data[@field='opacity']!=''">
                        <opacity>
                            <xsl:value-of select="data[@field='opacity']"/>
                        </opacity>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
        </properties>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_theme_data']">
        <!-- Theme Layer -->
        <xsl:variable name="geometry" select="./geometry/@value"/>
        <xsl:variable name="name" select="reference[@field='location_id']/text()"/>
        <xsl:variable name="value" select="data[@field='value']"/>

        <type>Feature</type>
        <geometry>
            <xsl:attribute name="value">
                <!-- Use pre-prepared GeoJSON -->
                <xsl:value-of select="$geometry"/>
            </xsl:attribute>
        </geometry>
        <properties>
            <id>
                <xsl:value-of select="@uuid"/>
            </id>
            <name>
                <xsl:value-of select="$name"/>
            </name>
            <value>
                <xsl:value-of select="$value"/>
            </value>
            <popup>
                <xsl:value-of select="concat($name, ': ', $value)"/>
            </popup>
        </properties>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource">
        <xsl:if test="./reference[@field='location_id']">
        <!-- Feature Layer -->

            <xsl:variable name="geometry" select="./geometry/@value"/>
            <xsl:variable name="wkt" select="./reference[@field='location_id']/@wkt"/>

            <xsl:choose>
                <xsl:when test="$geometry!='null'">
                    <!-- Use pre-prepared GeoJSON -->
                    <type>Feature</type>
                    <geometry>
                        <xsl:attribute name="value">
                            <xsl:value-of select="$geometry"/>
                        </xsl:attribute>
                    </geometry>
                    <properties>
                        <id>
                            <xsl:value-of select="reference[@field='location_id']/@uuid"/>
                        </id>
                        <xsl:choose>
                            <xsl:when test="data[@field='name']!=''">
                                <name>
                                    <xsl:value-of select="data[@field='name']"/>
                                </name>
                            </xsl:when>
                            <xsl:when test="reference[@field='location_id']/text()!=''">
                                <name>
                                    <xsl:value-of select="reference[@field='location_id']/text()"/>
                                </name>
                            </xsl:when>
                        </xsl:choose>
                        <xsl:if test="reference[@field='location_id']/@marker!=''">
                            <marker>
                                <xsl:value-of select="reference[@field='location_id']/@marker"/>
                            </marker>
                        </xsl:if>
                        <xsl:if test="reference[@field='location_id']/@popup!=''">
                            <popup>
                                <xsl:value-of select="reference[@field='location_id']/@popup"/>
                            </popup>
                        </xsl:if>
                        <xsl:if test="reference[@field='location_id']/@popup_url!=''">
                            <url>
                                <xsl:value-of select="reference[@field='location_id']/@popup_url"/>
                            </url>
                        </xsl:if>
                    </properties>
                </xsl:when>
                <xsl:when test="$wkt!='null'">
                    <!-- Convert WKT to GeoJSON in XSLT. Note that this can hit the libxslt default recursion limit
                         http://blog.gmane.org/gmane.comp.python.lxml.devel/day=20120309
                         This shouldn't be called any more but is left in as an example -->
                    <type>Feature</type>
                    <geometry>
                        <xsl:choose>
                            <xsl:when test="starts-with($wkt,'POINT')">
                                <type>
                                    <xsl:text>Point</xsl:text>
                                </type>
                                <coordinates>
                                    <xsl:attribute name="value">
                                        <xsl:call-template name="Point">
                                            <xsl:with-param name="point">
                                                <xsl:value-of select="substring-before(substring-after(normalize-space(substring-after($wkt,'POINT')),'('),')')"/>
                                            </xsl:with-param>
                                        </xsl:call-template>
                                    </xsl:attribute>
                                </coordinates>
                            </xsl:when>
                            <xsl:when test="starts-with($wkt,'LINESTRING')">
                                <type>
                                    <xsl:text>LineString</xsl:text>
                                </type>
                                <coordinates>
                                    <xsl:attribute name="value">
                                        <xsl:call-template name="LineString">
                                            <xsl:with-param name="linestring">
                                                <xsl:value-of select="normalize-space(substring-after($wkt,'LINESTRING'))"/>
                                            </xsl:with-param>
                                        </xsl:call-template>
                                    </xsl:attribute>
                                </coordinates>
                            </xsl:when>
                            <xsl:when test="starts-with($wkt,'POLYGON')">
                                <type>
                                    <xsl:text>Polygon</xsl:text>
                                </type>
                                <coordinates>
                                    <xsl:attribute name="value">
                                        <xsl:call-template name="Polygon">
                                            <xsl:with-param name="polygon">
                                                <xsl:value-of select="normalize-space(substring-after($wkt,'POLYGON'))"/>
                                            </xsl:with-param>
                                        </xsl:call-template>
                                    </xsl:attribute>
                                </coordinates>
                            </xsl:when>
                            <xsl:when test="starts-with($wkt,'MULTIPOLYGON')">
                                <type>
                                    <xsl:text>MultiPolygon</xsl:text>
                                </type>
                                <coordinates>
                                    <xsl:attribute name="value">
                                        <xsl:call-template name="MultiPolygon">
                                            <xsl:with-param name="multipolygon">
                                                <xsl:value-of select="normalize-space(substring-after($wkt,'MULTIPOLYGON'))"/>
                                            </xsl:with-param>
                                        </xsl:call-template>
                                    </xsl:attribute>
                                </coordinates>
                            </xsl:when>
                        </xsl:choose>
                    </geometry>
                    <properties>
                        <id>
                            <xsl:value-of select="reference[@field='location_id']/@uuid"/>
                        </id>
                        <xsl:choose>
                            <xsl:when test="data[@field='name']!=''">
                                <name>
                                    <xsl:value-of select="data[@field='name']"/>
                                </name>
                            </xsl:when>
                            <xsl:when test="reference[@field='location_id']/text()!=''">
                                <name>
                                    <xsl:value-of select="reference[@field='location_id']/text()"/>
                                </name>
                            </xsl:when>
                        </xsl:choose>
                        <xsl:if test="data[@field='value']!=''">
                            <!-- Theme Layer -->
                            <value>
                                <xsl:value-of select="data[@field='value']"/>
                            </value>
                        </xsl:if>
                        <xsl:if test="reference[@field='location_id']/@marker!=''">
                            <marker>
                                <xsl:value-of select="reference[@field='location_id']/@marker"/>
                            </marker>
                        </xsl:if>
                        <xsl:if test="reference[@field='location_id']/@popup!=''">
                            <popup>
                                <xsl:value-of select="reference[@field='location_id']/@popup"/>
                            </popup>
                        </xsl:if>
                        <xsl:if test="reference[@field='location_id']/@popup_url!=''">
                            <url>
                                <xsl:value-of select="reference[@field='location_id']/@popup_url"/>
                            </url>
                        </xsl:if>
                    </properties>
                </xsl:when>
                <xsl:when test="./reference[@field='location_id']/@lon!='null'">
                    <type>Feature</type>
                    <geometry>
                        <type>
                            <xsl:text>Point</xsl:text>
                        </type>
                        <coordinates>
                            <xsl:value-of select="reference[@field='location_id']/@lon"/>
                        </coordinates>
                        <coordinates>
                            <xsl:value-of select="reference[@field='location_id']/@lat"/>
                        </coordinates>
                    </geometry>
                    <properties>
                        <id>
                            <xsl:value-of select="reference[@field='location_id']/@uuid"/>
                        </id>
                        <name>
                            <xsl:value-of select="data[@field='name']"/>
                        </name>
                        <marker>
                            <xsl:value-of select="reference[@field='location_id']/@marker"/>
                        </marker>
                        <popup>
                            <xsl:value-of select="reference[@field='location_id']/@popup"/>
                        </popup>
                        <url>
                            <xsl:value-of select="reference[@field='location_id']/@popup_url"/>
                        </url>
                    </properties>
                </xsl:when>
                <!-- xsl:otherwise skip -->
            </xsl:choose>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Point">
        <xsl:param name="point"/>
        <xsl:variable name="lon" select="substring-before($point,' ')"/>
        <xsl:variable name="lat" select="substring-after($point,' ')"/>
        <xsl:value-of select="concat('[',$lon,', ',$lat,']')"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Points">
        <xsl:param name="points"/>
        <xsl:choose>
            <xsl:when test="contains($points,',')">
                <xsl:variable name="point" select="substring-before($points,',')"/>
                <xsl:variable name="remainder" select="normalize-space(substring-after($points,','))"/>
                <xsl:call-template name="Point">
                    <xsl:with-param name="point">
                        <xsl:value-of select="$point"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:text>, </xsl:text>
                <xsl:call-template name="Points">
                    <xsl:with-param name="points">
                        <xsl:value-of select="$remainder"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="Point">
                    <xsl:with-param name="point">
                        <xsl:value-of select="$points"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LineString">
        <xsl:param name="linestring"/>
        <xsl:text>[</xsl:text>
        <!-- Strip outer parentheses -->
        <xsl:variable name="points" select="substring-before(substring-after($linestring,'('),')')"/>
        <xsl:call-template name="Points">
            <xsl:with-param name="points">
                <xsl:value-of select="$points"/>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:text>]</xsl:text>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Rings">
        <xsl:param name="rings"/>
        <xsl:choose>
            <xsl:when test="contains($rings,'),(')">
                <xsl:variable name="ring" select="substring-before($rings,',(')"/>
                <xsl:variable name="remainder" select="normalize-space(substring-after($rings,'),'))"/>
                <xsl:call-template name="LineString">
                    <xsl:with-param name="linestring">
                        <xsl:value-of select="$ring"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:text>, </xsl:text>
                <xsl:call-template name="Rings">
                    <xsl:with-param name="rings">
                        <xsl:value-of select="$remainder"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="LineString">
                    <xsl:with-param name="linestring">
                        <xsl:value-of select="$rings"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Polygon">
        <xsl:param name="polygon"/>
        <xsl:text>[</xsl:text>
        <!-- Strip outer parentheses -->
        <xsl:variable name="rings" select="concat(substring-before(substring-after($polygon,'('),'))'),')')"/>
        <xsl:call-template name="Rings">
            <xsl:with-param name="rings">
                <xsl:value-of select="$rings"/>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:text>]</xsl:text>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Polygons">
        <xsl:param name="polygons"/>
        <xsl:choose>
            <xsl:when test="contains($polygons,'),(')">
                <xsl:variable name="polygon" select="substring-before($polygons,',(')"/>
                <xsl:variable name="remainder" select="normalize-space(substring-after($polygons,'),'))"/>
                <xsl:call-template name="Polygon">
                    <xsl:with-param name="polygon">
                        <xsl:value-of select="$polygon"/>
                    </xsl:with-param>
                </xsl:call-template>
                <xsl:text>, </xsl:text>
                <xsl:call-template name="Polygons">
                    <xsl:with-param name="polygons">
                        <xsl:value-of select="$remainder"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="Polygon">
                    <xsl:with-param name="polygon">
                        <xsl:value-of select="$polygons"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="MultiPolygon">
        <xsl:param name="multipolygon"/>
        <xsl:text>[</xsl:text>
        <!-- Strip outer parentheses -->
        <xsl:variable name="polygons" select="concat(substring-before(substring-after($multipolygon,'('),'))'),')')"/>
        <xsl:call-template name="Polygons">
            <xsl:with-param name="polygons">
                <xsl:value-of select="$polygons"/>
            </xsl:with-param>
        </xsl:call-template>
        <xsl:text>]</xsl:text>
    </xsl:template>

</xsl:stylesheet>
