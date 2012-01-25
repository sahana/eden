<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Google Layer - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Layer Name
         API Key..............string..........Layer API key (only needed for MapMaker & Earth)
         Maps.................boolean.........Layer Maps Enabled?
         Satellite............boolean.........Layer Satellite Enabled?
         Hybrid...............boolean.........Layer Hybrid Enabled?
         Streetview...........boolean.........Layer Streetview Enabled?
         Earth................boolean.........Layer Earth Enabled?

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
        <resource name="gis_layer_google">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="apikey"><xsl:value-of select="col[@field='API Key']"/></data>
            <data field="maps_enabled"><xsl:value-of select="col[@field='Maps']"/></data>
            <data field="satellite_enabled"><xsl:value-of select="col[@field='Satellite']"/></data>
            <data field="hybrid_enabled"><xsl:value-of select="col[@field='Hybrid']"/></data>
            <data field="streetview_enabled"><xsl:value-of select="col[@field='Streetview']"/></data>
            <data field="earth_enabled"><xsl:value-of select="col[@field='Earth']"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
