<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         GIS Configurations - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........gis_config.name
         Region...............string..........gis_config.region_location_id.name
         Default..............string..........gis_config.default_location_id.name
         Zoom.................integer.........gis_config.zoom
         Lat..................float...........gis_config.lat
         Lon..................float...........gis_config.lon
         L1...................string..........gis_config.L1 (Name for L1 locations)
         L2...................string..........gis_config.L2 (Name for L2 locations)
         L3...................string..........gis_config.L3 (Name for L3 locations)
         MinLat...............float...........gis_config.min_lat
         MaxLat...............float...........gis_config.max_lat
         MinLon...............float...........gis_config.min_lon
         MaxLon...............float...........gis_config.max_lon
         

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

        <xsl:variable name="region" select="col[@field='Region']/text()"/>
        <xsl:variable name="default" select="col[@field='Default']/text()"/>
    
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$region"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$region"/></data>
        </resource>
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$default"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$default"/></data>
        </resource>
        <resource name="gis_config">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="zoom"><xsl:value-of select="col[@field='Zoom']"/></data>
            <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
            <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
            <data field="L1"><xsl:value-of select="col[@field='L1']"/></data>
            <data field="L2"><xsl:value-of select="col[@field='L2']"/></data>
            <data field="L3"><xsl:value-of select="col[@field='L3']"/></data>
            <data field="min_lat"><xsl:value-of select="col[@field='MinLat']"/></data>
            <data field="min_lon"><xsl:value-of select="col[@field='MinLon']"/></data>
            <data field="max_lat"><xsl:value-of select="col[@field='MaxLat']"/></data>
            <data field="max_lon"><xsl:value-of select="col[@field='MaxLon']"/></data>
            <reference field="region_location_id" resource="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$region"/>
                </xsl:attribute>
            </reference>
            <reference field="default_location_id" resource="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$default"/>
                </xsl:attribute>
            </reference>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
