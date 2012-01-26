<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Feature Layers - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Layer Name
         Description..........string..........Layer Description
         Module...............string..........Layer Module
         Resource.............string..........Layer Resource
         Marker...............string..........Layer Marker Name
         GPS Marker...........string..........Layer GPS Marker
         Popup Label..........string..........Layer Popup Label
         Popup Fields.........string..........Layer Popup Fields
         REST Filter..........string..........Layer Filter (for Map JS calling back to server)
         Filter Field.........string..........Layer Filter Field (for exports to determine Marker)
         Filter Value.........string..........Layer Filter Value (for exports to determine Marker)
         Folder...............string..........Layer Folder
         Visible..............boolean.........Layer Visible?

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="markers" match="row" use="col[@field='Marker']/text()"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Markers -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('markers',
                                                                   col[@field='Marker'])[1])]">
                <xsl:call-template name="Marker"/>
            </xsl:for-each>

            <!-- Feature Layers -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Marker" select="col[@field='Marker']/text()"/>
    
        <resource name="gis_layer_feature">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <data field="module"><xsl:value-of select="col[@field='Module']"/></data>
            <data field="resource"><xsl:value-of select="col[@field='Resource']"/></data>
            <reference field="marker_id" resource="gis_marker">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Marker"/>
                </xsl:attribute>
            </reference>
            <data field="gps_marker"><xsl:value-of select="col[@field='GPS Marker']"/></data>
            <data field="filter"><xsl:value-of select="col[@field='REST Filter']"/></data>
            <data field="filter_field"><xsl:value-of select="col[@field='Filter Field']"/></data>
            <data field="filter_value"><xsl:value-of select="col[@field='Filter Value']"/></data>
            <data field="popup_label"><xsl:value-of select="col[@field='Popup Label']"/></data>
            <data field="popup_fields"><xsl:value-of select="col[@field='Popup Fields']"/></data>
            <data field="dir"><xsl:value-of select="col[@field='Folder']"/></data>
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

</xsl:stylesheet>
