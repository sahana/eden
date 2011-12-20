<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************

         GeoJSON Export Templates for Sahana-Eden

         Version 0.3 / 2011-05-13 / by flavour

         Copyright (c) 2011 Sahana Software Foundation

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
            <!--
            <popup>
                <xsl:value-of select="@popup"/>
            </popup>
            <url>
                <xsl:value-of select="@url"/>
            </url>
            -->
        </properties>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_feature_query']">
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
                </xsl:otherwise>
            </xsl:choose>
        </properties>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource">
        <xsl:if test="./reference[@field='location_id']">
            <!-- Skip records without LatLon -->
            <xsl:if test="./reference[@field='location_id']/@lon!='null'">
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
                        <xsl:value-of select="reference[@field='location_id']/@url"/>
                    </url>
                </properties>
            </xsl:if>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>
