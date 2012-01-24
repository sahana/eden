<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         TMS Layers - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Layer Name
         Description..........string..........Layer Description
         Enabled..............boolean.........Layer Enabled?
         Folder...............string..........Layer Folder
         URL..................string..........Layer URL
         URL2.................string..........Layer URL2
         URL3.................string..........Layer URL3
         Layer Name...........string..........Layer LayerName
         Format...............string..........Layer Image Format
         Attribution..........string..........Layer Attribution
         Zoom Levels..........integer.........Layer Zoom Levels

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
        <resource name="gis_layer_tms">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <data field="enabled"><xsl:value-of select="col[@field='Enabled']"/></data>
            <data field="dir"><xsl:value-of select="col[@field='Folder']"/></data>
            <data field="url"><xsl:value-of select="col[@field='URL']"/></data>
            <data field="url2"><xsl:value-of select="col[@field='URL2']"/></data>
            <data field="url3"><xsl:value-of select="col[@field='URL3']"/></data>
            <data field="layername"><xsl:value-of select="col[@field='Layer Name']"/></data>
            <xsl:if test="col[@field='Format']!=''">
                <data field="img_format"><xsl:value-of select="col[@field='Format']"/></data>
            </xsl:if>
            <data field="attribution"><xsl:value-of select="col[@field='Attribution']"/></data>
            <data field="zoom_levels"><xsl:value-of select="col[@field='Zoom Levels']"/></data>
        </resource>
    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
