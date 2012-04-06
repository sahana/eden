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
         Config...............string..........Configuration Name
         Enabled..............boolean.........Layer Enabled in config? (SITE_DEFAULT if not-specified)
         Visible..............boolean.........Layer Visible in config? (SITE_DEFAULT if not-specified)
         Folder...............string..........Layer Folder
         Base.................boolean.........Layer Base?
         Transparent..........boolean.........Layer Transparent?
         Opacity..............double..........Layer Opacity
         Format...............string..........Layer Image Format
         Queryable............boolean.........Layer Queryable?
         LegendURL............string..........Layer LegendURL
         Tiled................boolean.........Layer Tiled?
         Style................string..........Layer Style
         Map..................string..........Layer Map (not usually required)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="configs" match="row" use="col[@field='Config']/text()"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Configs -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('configs',
                                                                   col[@field='Config'])[1])]">
                <xsl:call-template name="Config"/>
            </xsl:for-each>

            <!-- Layers -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Layer" select="col[@field='Name']/text()"/>
        <xsl:variable name="Config" select="col[@field='Config']/text()"/>

        <resource name="gis_layer_wms">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Layer"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Layer"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <data field="url"><xsl:value-of select="col[@field='URL']"/></data>
            <data field="layers"><xsl:value-of select="col[@field='Layers']"/></data>
            <data field="dir"><xsl:value-of select="col[@field='Folder']"/></data>
            <data field="base"><xsl:value-of select="col[@field='Base']"/></data>
            <data field="transparent"><xsl:value-of select="col[@field='Transparent']"/></data>
            <data field="opacity"><xsl:value-of select="col[@field='Opacity']"/></data>
            <data field="img_format"><xsl:value-of select="col[@field='Format']"/></data>
            <data field="queryable"><xsl:value-of select="col[@field='Queryable']"/></data>
            <data field="legend_url"><xsl:value-of select="col[@field='LegendURL']"/></data>
            <data field="tiled"><xsl:value-of select="col[@field='Tiled']"/></data>
            <data field="style"><xsl:value-of select="col[@field='Style']"/></data>
            <data field="map"><xsl:value-of select="col[@field='Map']"/></data>
        </resource>

        <resource name="gis_layer_config">
            <reference field="layer_id" resource="gis_layer_wms">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Layer"/>
                </xsl:attribute>
            </reference>
            <reference field="config_id" resource="gis_config">
                <xsl:choose>
                    <xsl:when test="$Config!=''">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$Config"/>
                        </xsl:attribute>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="'SITE_DEFAULT'"/>
                        </xsl:attribute>
                    </xsl:otherwise>
                </xsl:choose>
            </reference>
            <data field="enabled"><xsl:value-of select="col[@field='Enabled']"/></data>
            <data field="visible"><xsl:value-of select="col[@field='Visible']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template name="Config">

        <xsl:variable name="Config" select="col[@field='Config']/text()"/>
    
        <resource name="gis_config">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Config"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Config"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
