<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Capacity Indicators - CSV Import Stylesheet

         CSV column...........Format..........Content

         Section..............string..........Indicator Section
         Header...............string..........Indicator Header
         Number...............integer.........Indicator Number
         Name.................string..........Indicator Name

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
        <resource name="org_capacity_indicator">
            <data field="section"><xsl:value-of select="col[@field='Section']"/></data>
            <data field="header"><xsl:value-of select="col[@field='Header']"/></data>
            <data field="number"><xsl:value-of select="col[@field='Number']"/></data>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
