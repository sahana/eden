<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         WMS Layers - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Layer Name
         Description..........string..........Layer Description
         URL..................string..........Layer URL
         Layers...............string..........Layers
         Enabled..............boolean.........Layer Enabled?
         Visible..............boolean.........Layer Visible?
         Folder...............string..........Layer Folder
         Base.................boolean.........Layer Base?
         Transparent..........boolean.........Layer Transparent?
         Opacity..............double..........Layer Opacity
         Format...............string..........Layer Image Format
         Tiled................boolean.........Layer Tiled?
         Style................string..........Layer Style
         Map..................string..........Layer Map (not usually required)

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
        <resource name="gis_layer_wms">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <data field="url"><xsl:value-of select="col[@field='URL']"/></data>
            <data field="layers"><xsl:value-of select="col[@field='Layers']"/></data>
            <data field="enabled"><xsl:value-of select="col[@field='Enabled']"/></data>
            <data field="visible"><xsl:value-of select="col[@field='Visible']"/></data>
            <data field="dir"><xsl:value-of select="col[@field='Folder']"/></data>
            <data field="base"><xsl:value-of select="col[@field='Base']"/></data>
            <data field="transparent"><xsl:value-of select="col[@field='Transparent']"/></data>
            <data field="opacity"><xsl:value-of select="col[@field='Opacity']"/></data>
            <data field="img_format"><xsl:value-of select="col[@field='Format']"/></data>
            <data field="tiled"><xsl:value-of select="col[@field='Tiled']"/></data>
            <data field="style"><xsl:value-of select="col[@field='Style']"/></data>
            <data field="map"><xsl:value-of select="col[@field='Map']"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
