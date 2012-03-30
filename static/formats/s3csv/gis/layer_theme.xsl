<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Theme Layers - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Layer Name
         Description..........string..........Layer Description
         Enabled..............boolean.........Layer Enabled in SITE_DEFAULT config?
         Visible..............boolean.........Layer Visible in SITE_DEFAULT config?
         Folder...............string..........Layer Folder
         Date.................date............Layer Date

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Layer" select="col[@field='Name']/text()"/>

        <resource name="gis_layer_theme">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Layer"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Layer"/></data>
            <xsl:if test="col[@field='Description']!=''">
                <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Folder']!=''">
                <data field="dir"><xsl:value-of select="col[@field='Folder']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Date']!=''">
                <data field="date"><xsl:value-of select="col[@field='Date']"/></data>
            </xsl:if>
        </resource>

        <resource name="gis_layer_config">
            <reference field="layer_id" resource="gis_layer_theme">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Layer"/>
                </xsl:attribute>
            </reference>
            <reference field="config_id" resource="gis_config">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="'SITE_DEFAULT'"/>
                </xsl:attribute>
            </reference>
            <data field="enabled"><xsl:value-of select="col[@field='Enabled']"/></data>
            <data field="visible"><xsl:value-of select="col[@field='Visible']"/></data>
        </resource>

    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
