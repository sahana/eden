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
            <xsl:attribute name="upload">true</xsl:attribute>
            <xsl:attribute name="generator">Sahana Eden</xsl:attribute>
            <xsl:apply-templates select="s3xml"/>
        </osm>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="/s3xml">
        <xsl:variable name="domain" select="@domain" />
        <!--
        <bounds>
            <xsl:attribute name="minlat"><xsl:value-of select="@latmin"/></xsl:attribute>
            <xsl:attribute name="minlon"><xsl:value-of select="@lonmin"/></xsl:attribute>
            <xsl:attribute name="maxlat"><xsl:value-of select="@latmax"/></xsl:attribute>
            <xsl:attribute name="maxlon"><xsl:value-of select="@lonmax"/></xsl:attribute>
        </bounds>
        -->
        <xsl:apply-templates select=".//resource"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource">
        <xsl:choose>
            <xsl:when test="@name='gis_location'">
                <xsl:if test="./data[@field='level']='L3' or ./data[@field='level']='L4'">
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
                                <xsl:value-of select="@uuid"/>
                            </xsl:attribute>
                        </tag>
                        <tag>
                            <xsl:attribute name="k">sahana</xsl:attribute>
                            <xsl:attribute name="v">
                                <xsl:value-of select="@url"/>
                            </xsl:attribute>
                        </tag>
                        <tag>
                            <xsl:attribute name="k">name</xsl:attribute>
                            <xsl:attribute name="v"><xsl:value-of select="data[@field='name']"/></xsl:attribute>
                        </tag>
                        <tag>
                            <!-- @ToDo: Vary this by country -->
                            <xsl:choose>
                                <xsl:when test="./data[@field='level']='L3'">
                                    <xsl:attribute name="k">place</xsl:attribute>
                                    <xsl:attribute name="v">town</xsl:attribute>
                                </xsl:when>
                            </xsl:choose>
                            <xsl:choose>
                                <xsl:when test="./data[@field='level']='L4'">
                                    <xsl:attribute name="k">place</xsl:attribute>
                                    <xsl:attribute name="v">village</xsl:attribute>
                                </xsl:when>
                            </xsl:choose>
                        </tag>
                    </node>
                </xsl:if>
            </xsl:when>
            <xsl:when test="reference[@field='location_id']">
                <xsl:variable name="lat">
                    <xsl:value-of select="reference[@field='location_id']/@lat"/>
                </xsl:variable>
                <xsl:variable name="lon">
                    <xsl:value-of select="reference[@field='location_id']/@lon"/>
                </xsl:variable>
                <xsl:variable name="name">
                    <xsl:value-of select="./data[@field='name']"/>
                </xsl:variable>
                <xsl:if test="$lat!='' and $lon!='' and $name!=''">
                    <node>
                        <xsl:variable name="id" select='position()' />
                        <xsl:attribute name="id">
                            <xsl:text>-</xsl:text>
                            <xsl:value-of select="$id" />
                        </xsl:attribute>
                        <xsl:attribute name="lat"><xsl:value-of select="$lat"/></xsl:attribute>
                        <xsl:attribute name="lon"><xsl:value-of select="$lon"/></xsl:attribute>
                        <tag>
                            <xsl:attribute name="k">id:uuid</xsl:attribute>
                            <xsl:attribute name="v">
                                <xsl:value-of select="@uuid"/>
                            </xsl:attribute>
                        </tag>
                        <tag>
                            <xsl:attribute name="k">name</xsl:attribute>
                            <xsl:attribute name="v"><xsl:value-of select="$name"/></xsl:attribute>
                        </tag>
                        <tag>
                            <xsl:choose>
                                <xsl:when test="@name='cr_shelter'">
                                    <xsl:attribute name="k">refugee</xsl:attribute>
                                    <xsl:attribute name="v">yes</xsl:attribute>
                                </xsl:when>
                                <xsl:when test="@name='hms_hospital'">
                                    <xsl:attribute name="k">amenity</xsl:attribute>
                                    <xsl:attribute name="v">hospital</xsl:attribute>
                                </xsl:when>
                                <xsl:when test="@name='transport_airport'">
                                    <xsl:attribute name="k">aeroway</xsl:attribute>
                                    <xsl:attribute name="v">aerodrome</xsl:attribute>
                                </xsl:when>
                                <xsl:when test="@name='transport_seaport'">
                                    <xsl:attribute name="k">harbour</xsl:attribute>
                                    <xsl:attribute name="v">yes</xsl:attribute>
                                </xsl:when>
                                <xsl:when test="@name='org_facility'">
                                    <xsl:choose>
                                        <xsl:when test="reference[@field='facility_type_id']='Church'">
                                            <xsl:attribute name="k">amenity</xsl:attribute>
                                            <xsl:attribute name="v">place_of_worship</xsl:attribute>
                                        </xsl:when>
                                        <xsl:when test="reference[@field='facility_type_id']='School'">
                                            <xsl:attribute name="k">amenity</xsl:attribute>
                                            <xsl:attribute name="v">school</xsl:attribute>
                                        </xsl:when>
                                    </xsl:choose>
                                </xsl:when>
                                <xsl:when test="@name='org_office'">
                                    <!-- @ToDo: Vary this by Organisation Type -->
                                    <xsl:attribute name="k">office</xsl:attribute>
                                    <xsl:attribute name="v">ngo</xsl:attribute>
                                </xsl:when>
                            </xsl:choose>
                        </tag>
                    </node>
                </xsl:if>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>