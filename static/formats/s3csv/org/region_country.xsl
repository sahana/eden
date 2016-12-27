<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Regions - CSV Import Stylesheet

         CSV column...........Format..........Content

         Parent...............string..........Region Parent
         Region...............string..........Region Name
         Country..............string..........Country
         Comments.............string..........Comments

    *********************************************************************** -->
    <xsl:import href="../commons.xsl"/>

    <xsl:output method="xml"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="parent" match="row" use="col[@field='Parent']"/>
    <xsl:key name="region" match="row" use="concat(col[@field='Parent'],
                                                   col[@field='Region'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Parent Regions -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('parent',
                                                                       col[@field='Parent'])[1])]">
                <xsl:call-template name="Region">
                    <xsl:with-param name="RegionName">
                        <xsl:value-of select="col[@field='Parent']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Regions -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('region',
                                                                       concat(col[@field='Parent'],
                                                                              col[@field='Region']))[1])]">
                <xsl:call-template name="Region">
                    <xsl:with-param name="ParentName">
                        <xsl:value-of select="col[@field='Parent']"/>
                    </xsl:with-param>
                    <xsl:with-param name="RegionName">
                        <xsl:value-of select="col[@field='Region']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Countries -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template match="row">
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:if test="$l0!=''">
            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$l0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

            <resource name="org_region_country">
                <reference field="region_id" resource="org_region">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='Region']"/>
                    </xsl:attribute>
                </reference>
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
                <xsl:if test="col[@field='Comments']!=''">
                    <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
                </xsl:if>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Region">
        <xsl:param name="RegionName"/>
        <xsl:param name="ParentName"/>

        <xsl:if test="$RegionName!=''">
            <resource name="org_region">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$RegionName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$RegionName"/></data>
                <xsl:if test="$ParentName!=''">
                    <reference field="parent" resource="org_region">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$ParentName"/>
                        </xsl:attribute>
                    </reference>
                    <xsl:if test="col[@field='Country']=''">
                        <!-- Comments are for the region -->
                        <xsl:if test="col[@field='Comments']!=''">
                            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
                        </xsl:if>
                    </xsl:if>
                </xsl:if>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
