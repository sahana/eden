<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Bing Layer - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Layer Name
         API Key..............string..........Layer API key
         Enabled..............boolean.........Layer Enabled?

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
        <resource name="gis_layer_bing">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="apikey"><xsl:value-of select="col[@field='API Key']"/></data>
            <data field="enabled"><xsl:value-of select="col[@field='Enabled']"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
