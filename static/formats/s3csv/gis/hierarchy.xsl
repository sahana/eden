<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         GIS Hierarchy - CSV Import Stylesheet

         CSV column...........Format..........Content

         UID..................string..........gis_hierarchy.uuid (needed for SITE_DEFAULT)
         Country..............string..........gis_hierarchy.location_id
         L1...................string..........gis_hierarchy.L1 (Label for L1 locations)
         L2...................string..........gis_hierarchy.L2 (Label for L2 locations)
         L3...................string..........gis_hierarchy.L3 (Label for L3 locations)
         L4...................string..........gis_hierarchy.L4 (Label for L4 locations)
         L5...................string..........gis_hierarchy.L5 (Label for L5 locations)
         Edit L1..............boolean.........gis_hierarchy.edit_L1
         Edit L2..............boolean.........gis_hierarchy.edit_L2
         Edit L3..............boolean.........gis_hierarchy.edit_L4
         Edit L4..............boolean.........gis_hierarchy.edit_L4

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Hierarchies -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template match="row">

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
    
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

        <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

        <resource name="gis_hierarchy">
            <xsl:if test="col[@field='UUID']!=''">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="col[@field='UUID']"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="$l0!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <data field="L1"><xsl:value-of select="col[@field='L1']"/></data>
            <data field="L2"><xsl:value-of select="col[@field='L2']"/></data>
            <data field="L3"><xsl:value-of select="col[@field='L3']"/></data>
            <data field="L4"><xsl:value-of select="col[@field='L4']"/></data>
            <data field="L5"><xsl:value-of select="col[@field='L5']"/></data>
            <xsl:if test="col[@field='Edit L1']!=''">
                <data field="edit_L1"><xsl:value-of select="col[@field='Edit L1']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Edit L2']!=''">
                <data field="edit_L2"><xsl:value-of select="col[@field='Edit L2']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Edit L3']!=''">
                <data field="edit_L3"><xsl:value-of select="col[@field='Edit L3']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Edit L4']!=''">
                <data field="edit_L4"><xsl:value-of select="col[@field='Edit L4']"/></data>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
