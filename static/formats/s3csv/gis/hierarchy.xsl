<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         GIS Hierarchy - CSV Import Stylesheet

         CSV column...........Format..........Content

         UID..................string..........gis_hierarchy.uuid (needed for SITE_DEFAULT)
         L1...................string..........gis_hierarchy.L1 (Label for L1 locations)
         L2...................string..........gis_hierarchy.L2 (Label for L2 locations)
         L3...................string..........gis_hierarchy.L3 (Label for L3 locations)
         L4...................string..........gis_hierarchy.L4 (Label for L4 locations)
         Edit L1..............boolean.........gis_hierarchy.edit_L1
         

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Hierarchies -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template match="row">
        <resource name="gis_hierarchy">
            <xsl:if test="col[@field='UUID']!=''">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="col[@field='UUID']"/>
                </xsl:attribute>
            </xsl:if>
            <data field="L1"><xsl:value-of select="col[@field='L1']"/></data>
            <data field="L2"><xsl:value-of select="col[@field='L2']"/></data>
            <data field="L3"><xsl:value-of select="col[@field='L3']"/></data>
            <data field="L4"><xsl:value-of select="col[@field='L4']"/></data>
            <xsl:if test="col[@field='Edit L1']!=''">
                <data field="edit_L1"><xsl:value-of select="col[@field='Edit L1']"/></data>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
