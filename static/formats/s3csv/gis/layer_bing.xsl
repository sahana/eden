<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Bing Layer - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Layer Name
         Type.................string..........Layer Type
         Enabled..............boolean.........Layer Enabled in SITE_DEFAULT config?

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

        <resource name="gis_layer_bing">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Layer"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Layer"/></data>
            <data field="type"><xsl:value-of select="col[@field='Type']"/></data>
        </resource>

        <resource name="gis_layer_config">
            <reference field="layer_id" resource="gis_layer_bing">
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
        </resource>

    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
