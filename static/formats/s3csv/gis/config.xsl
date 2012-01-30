<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         GIS Configurations - CSV Import Stylesheet

         CSV column...........Format..........Content

         UID..................string..........gis_config.uuid (needed for SITE_DEFAULT)
         Name.................string..........gis_config.name
         Region...............string..........gis_config.region_location_id.name
         Default..............string..........gis_config.default_location_id.name
         Zoom.................integer.........gis_config.zoom
         Lat..................float...........gis_config.lat
         Lon..................float...........gis_config.lon
         L1...................string..........gis_config.L1 (Name for L1 locations)
         L2...................string..........gis_config.L2 (Name for L2 locations)
         L3...................string..........gis_config.L3 (Name for L3 locations)
         L4...................string..........gis_config.L4 (Name for L4 locations)
         Projection...........integer.........gis_config.projection.epsg
         Symbology............string..........gis_config.symbology_id
         Marker...............string..........gis_config.marker_id
         MinLat...............float...........gis_config.min_lat
         MaxLat...............float...........gis_config.max_lat
         MinLon...............float...........gis_config.min_lon
         MaxLon...............float...........gis_config.max_lon
         Search Level.........string..........gis_config.search_level
         WMS Browser..........float...........gis_config.wmsbrowser_url
         

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="markers" match="row" use="col[@field='Marker']/text()"/>
    <xsl:key name="projections" match="row" use="col[@field='Projection']/text()"/>
    <xsl:key name="symbologies" match="row" use="col[@field='Symbology']/text()"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Markers -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('markers',
                                                                   col[@field='Marker'])[1])]">
                <xsl:call-template name="Marker"/>
            </xsl:for-each>

            <!-- Projections -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('projections',
                                                                   col[@field='Projection'])[1])]">
                <xsl:call-template name="Projection"/>
            </xsl:for-each>

            <!-- Symbologies -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('symbologies',
                                                                   col[@field='Symbology'])[1])]">
                <xsl:call-template name="Symbology"/>
            </xsl:for-each>

            <!-- Configs -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template match="row">

        <xsl:variable name="region" select="col[@field='Region']/text()"/>
        <xsl:variable name="default" select="col[@field='Default']/text()"/>
        <xsl:variable name="Marker" select="col[@field='Marker']/text()"/>
        <xsl:variable name="Projection" select="col[@field='Projection']/text()"/>
        <xsl:variable name="Symbology" select="col[@field='Symbology']/text()"/>
    
        <xsl:if test="$region!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$region"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$region"/></data>
            </resource>
        </xsl:if>
        <xsl:if test="$default!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$default"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$default"/></data>
            </resource>
        </xsl:if>
        <resource name="gis_config">
            <xsl:if test="col[@field='UUID']!=''">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="col[@field='UUID']"/>
                </xsl:attribute>
            </xsl:if>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="zoom"><xsl:value-of select="col[@field='Zoom']"/></data>
            <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
            <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
            <data field="L1"><xsl:value-of select="col[@field='L1']"/></data>
            <data field="L2"><xsl:value-of select="col[@field='L2']"/></data>
            <data field="L3"><xsl:value-of select="col[@field='L3']"/></data>
            <data field="L4"><xsl:value-of select="col[@field='L4']"/></data>
            <data field="min_lat"><xsl:value-of select="col[@field='MinLat']"/></data>
            <data field="min_lon"><xsl:value-of select="col[@field='MinLon']"/></data>
            <data field="max_lat"><xsl:value-of select="col[@field='MaxLat']"/></data>
            <data field="max_lon"><xsl:value-of select="col[@field='MaxLon']"/></data>
            <xsl:if test="col[@field='Search Level']!=''">
                <data field="search_level"><xsl:value-of select="col[@field='Search Level']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='WMS Browser']!=''">
                <data field="wmsbrowser_url"><xsl:value-of select="col[@field='WMS Browser']"/></data>
            </xsl:if>
            <reference field="marker_id" resource="gis_marker">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Marker"/>
                </xsl:attribute>
            </reference>
            <reference field="projection_id" resource="gis_projection">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Projection"/>
                </xsl:attribute>
            </reference>
            <reference field="symbology_id" resource="gis_symbology">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Symbology"/>
                </xsl:attribute>
            </reference>
            <xsl:if test="$region!=''">
                <reference field="region_location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$region"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="$default!=''">
                <reference field="default_location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$default"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template name="Marker">

        <xsl:variable name="Marker" select="col[@field='Marker']/text()"/>
    
        <resource name="gis_marker">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Marker"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Marker"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template name="Projection">

        <xsl:variable name="Projection" select="col[@field='Projection']/text()"/>
    
        <resource name="gis_projection">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Projection"/>
            </xsl:attribute>
            <data field="epsg"><xsl:value-of select="$Projection"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template name="Symbology">

        <xsl:variable name="Symbology" select="col[@field='Symbology']/text()"/>
    
        <resource name="gis_symbology">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Symbology"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Symbology"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
