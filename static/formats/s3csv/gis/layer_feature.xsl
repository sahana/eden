<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Feature Layers - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Layer Name
         Description..........string..........Layer Description
         Symbology............string..........Symbology Name
         Marker...............string..........Layer Symbology Marker Name
         GPS Marker...........string..........Layer Symbology GPS Marker
         Module...............string..........Layer Module
         Resource.............string..........Layer Resource
         Popup Label..........string..........Layer Popup Label
         Popup Fields.........string..........Layer Popup Fields
         REST Filter..........string..........Layer Filter (for Map JS calling back to server)
         Filter Field.........string..........Layer Filter Field (for exports to determine Marker)
         Filter Value.........string..........Layer Filter Value (for exports to determine Marker)
         Trackable............boolean.........Layer Trackable
         Folder...............string..........Layer Folder
         Enabled..............boolean.........Layer Enabled in SITE_DEFAULT config?
         Visible..............boolean.........Layer Visible in SITE_DEFAULT config?

         Needs Importing twice:
            layer_config
            layer_symbology

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="layers" match="row" use="col[@field='Name']/text()"/>
    <xsl:key name="markers" match="row" use="col[@field='Marker']/text()"/>
    <xsl:key name="symbologies" match="row" use="col[@field='Symbology']/text()"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Feature Layers -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('layers',
                                                                   col[@field='Name'])[1])]">
                <xsl:call-template name="Layer"/>
            </xsl:for-each>

            <!-- Markers -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('markers',
                                                                   col[@field='Marker'])[1])]">
                <xsl:call-template name="Marker"/>
            </xsl:for-each>

            <!-- Symbologies -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('symbologies',
                                                                   col[@field='Symbology'])[1])]">
                <xsl:call-template name="Symbology"/>
            </xsl:for-each>

            <!-- Layer Symbologies -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="gis_layer_symbology">
            <reference field="layer_id" resource="gis_layer_feature">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Name']"/>
                </xsl:attribute>
            </reference>
            <reference field="symbology_id" resource="gis_symbology">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Symbology']"/>
                </xsl:attribute>
            </reference>
            <reference field="marker_id" resource="gis_marker">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Marker']"/>
                </xsl:attribute>
            </reference>
            <data field="gps_marker"><xsl:value-of select="col[@field='GPS Marker']"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template name="Layer">

        <xsl:variable name="Layer" select="col[@field='Name']/text()"/>

        <resource name="gis_layer_feature">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Layer"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Layer"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <data field="module"><xsl:value-of select="col[@field='Module']"/></data>
            <data field="resource"><xsl:value-of select="col[@field='Resource']"/></data>
            <xsl:if test="col[@field='Trackable']">
                <data field="trackable"><xsl:value-of select="col[@field='Trackable']"/></data>
            </xsl:if>
            <data field="filter"><xsl:value-of select="col[@field='REST Filter']"/></data>
            <data field="filter_field"><xsl:value-of select="col[@field='Filter Field']"/></data>
            <data field="filter_value"><xsl:value-of select="col[@field='Filter Value']"/></data>
            <data field="popup_label"><xsl:value-of select="col[@field='Popup Label']"/></data>
            <data field="popup_fields"><xsl:value-of select="col[@field='Popup Fields']"/></data>
            <data field="dir"><xsl:value-of select="col[@field='Folder']"/></data>
        </resource>

        <resource name="gis_layer_config">
            <reference field="layer_id" resource="gis_layer_feature">
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
