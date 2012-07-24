<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns="http://openstreetmap.org/osm/0.6">

    <!-- **********************************************************************

         OpenStreetMap Export Templates for S3XML

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

    <xsl:output method="xml" indent="yes"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <osm>
            <xsl:attribute name="version">0.6</xsl:attribute>
            <xsl:attribute name="generator">Sahana Eden</xsl:attribute>
            <xsl:apply-templates select="s3xml"/>
        </osm>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="/s3xml">
        <xsl:variable name="domain" select="@domain" />
        <bounds>
            <xsl:attribute name="minlat"><xsl:value-of select="@latmin"/></xsl:attribute>
            <xsl:attribute name="minlon"><xsl:value-of select="@lonmin"/></xsl:attribute>
            <xsl:attribute name="maxlat"><xsl:value-of select="@latmax"/></xsl:attribute>
            <xsl:attribute name="maxlon"><xsl:value-of select="@lonmax"/></xsl:attribute>
        </bounds>
        <xsl:apply-templates select=".//resource[@name='gis_location']"/>
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
                <node>
                    <xsl:variable name="id" select='position()' />
                    <xsl:attribute name="id">
                        <xsl:text>-</xsl:text>
                        <xsl:value-of select="$id" />
                    </xsl:attribute>
                    <xsl:attribute name="lat"><xsl:value-of select="data[@field='lat']"/></xsl:attribute>
                    <xsl:attribute name="lon"><xsl:value-of select="data[@field='lon']"/></xsl:attribute>
                    <tag>
                        <xsl:attribute name="k">id:uuid</xsl:attribute>
                        <xsl:attribute name="v">
                            <!--<xsl:value-of select="$domain"/>
                            <xsl:text>/</xsl:text>-->
                            <xsl:value-of select="@uuid"/>
                        </xsl:attribute>
                    </tag>
                    <tag>
                        <xsl:attribute name="k">name</xsl:attribute>
                        <xsl:attribute name="v"><xsl:value-of select="./data[@field='name']"/></xsl:attribute>
                    </tag>
                    <tag>
                        <xsl:choose>
                            <xsl:when test="reference[@field='feature_class_id']='Town'">
                                <xsl:attribute name="k">place</xsl:attribute>
                                <xsl:attribute name="v">town</xsl:attribute>
                            </xsl:when>
                            <xsl:when test="reference[@field='feature_class_id']='Airport'">
                                <xsl:attribute name="k">aeroway</xsl:attribute>
                                <xsl:attribute name="v">aerodrome</xsl:attribute>
                            </xsl:when>
                            <xsl:when test="reference[@field='feature_class_id']='Bridge'">
                                <xsl:attribute name="k">highway</xsl:attribute>
                                <xsl:attribute name="v">road</xsl:attribute>
                                <xsl:attribute name="k">bridge</xsl:attribute>
                                <xsl:attribute name="v">yes</xsl:attribute>
                            </xsl:when>
                            <xsl:when test="reference[@field='feature_class_id']='Hospital'">
                                <xsl:attribute name="k">amenity</xsl:attribute>
                                <xsl:attribute name="v">hospital</xsl:attribute>
                            </xsl:when>
                            <xsl:when test="reference[@field='feature_class_id']='Church'">
                                <xsl:attribute name="k">amenity</xsl:attribute>
                                <xsl:attribute name="v">place_of_worship</xsl:attribute>
                            </xsl:when>
                            <xsl:when test="reference[@field='feature_class_id']='School'">
                                <xsl:attribute name="k">amenity</xsl:attribute>
                                <xsl:attribute name="v">school</xsl:attribute>
                            </xsl:when>
                        </xsl:choose>
                    </tag>
                </node>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource">
        <xsl:if test="reference[@field='location_id']">
            <node>
                <xsl:variable name="id" select='position()' />
                <xsl:attribute name="id">
                    <xsl:text>-</xsl:text>
                    <xsl:value-of select="$id" />
                </xsl:attribute>
                <xsl:attribute name="lat"><xsl:value-of select="reference[@field='location_id']/@lat"/></xsl:attribute>
                <xsl:attribute name="lon"><xsl:value-of select="reference[@field='location_id']/@lon"/></xsl:attribute>
                <tag>
                    <xsl:attribute name="k">id:uuid</xsl:attribute>
                    <xsl:attribute name="v">
                        <!--<xsl:value-of select="$domain"/>
                        <xsl:text>/</xsl:text>-->
                        <xsl:value-of select="@uuid"/>
                    </xsl:attribute>
                </tag>
                <tag>
                    <xsl:attribute name="k">name</xsl:attribute>
                    <xsl:attribute name="v"><xsl:value-of select="./data[@field='name']"/></xsl:attribute>
                </tag>
                <tag>
                    <xsl:choose>
                        <xsl:when test="@name='hms_hospital'">
                            <xsl:attribute name="k">amenity</xsl:attribute>
                            <xsl:attribute name="v">hospital</xsl:attribute>
                        </xsl:when>
                    </xsl:choose>
                </tag>
            </node>
        </xsl:if>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
