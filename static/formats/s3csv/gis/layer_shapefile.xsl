<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Shapefile Layers - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Layer Name
         Description..........string..........Layer Description
         Source Name..........string..........Layer Source Name
         Source URL...........string..........Layer Source URL
         Shapefile............string..........Layer Shapefile (URL to download)
         Projection...........string..........Layer Projection (Mandatory)
         Style................string..........Layer Style
         Symbology............string..........Symbology Name
         Marker...............string..........Layer Symbology Marker Name
         Filter...............string..........Layer Filter
         Folder...............string..........Layer Folder
         Config...............string..........Configuration Name
         Enabled..............boolean.........Layer Enabled in config? (SITE_DEFAULT if not-specified)
         Visible..............boolean.........Layer Enabled in config? (SITE_DEFAULT if not-specified)
         Cluster Distance.....integer.........Layer Cluster Distance: The number of pixels apart that features need to be before they are clustered (default=20)
         Cluster Threshold....integer.........Layer Cluster Threshold: The minimum number of features to form a cluster (default=2)

         Needs Importing twice:
            layer_config
            layer_symbology

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="configs" match="row" use="col[@field='Config']/text()"/>
    <xsl:key name="layers" match="row" use="col[@field='Name']/text()"/>
    <xsl:key name="markers" match="row" use="col[@field='Marker']/text()"/>
    <xsl:key name="projections" match="row" use="col[@field='Projection']/text()"/>
    <xsl:key name="symbologies" match="row" use="col[@field='Symbology']/text()"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Configs -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('configs',
                                                                   col[@field='Config'])[1])]">
                <xsl:call-template name="Config"/>
            </xsl:for-each>

            <!-- Layers -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('layers',
                                                                   col[@field='Name'])[1])]">
                <xsl:call-template name="Layer"/>
            </xsl:for-each>

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

            <!-- Layer Symbologies -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Symbology" select="col[@field='Symbology']/text()"/>

        <xsl:if test="$Symbology!=''">
            <resource name="gis_layer_symbology">
                <reference field="layer_id" resource="gis_layer_shapefile">
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
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Config">

        <xsl:variable name="Config" select="col[@field='Config']/text()"/>
    
        <xsl:if test="$Config!=''">
            <resource name="gis_config">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Config"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Config"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Layer">

        <xsl:variable name="Layer" select="col[@field='Name']/text()"/>
        <xsl:variable name="Config" select="col[@field='Config']/text()"/>

        <resource name="gis_layer_shapefile">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Layer"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Layer"/></data>
            <data field="shape">
                <xsl:attribute name="url">
                    <xsl:value-of select="col[@field='Shapefile']"/>
                </xsl:attribute>
            </data>
            <reference field="projection_id" resource="gis_projection">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Projection']"/>
                </xsl:attribute>
            </reference>
            <xsl:if test="col[@field='Description']!=''">
                <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            </xsl:if>
            <data field="source_name"><xsl:value-of select="col[@field='Source Name']"/></data>
            <data field="source_url"><xsl:value-of select="col[@field='Source URL']"/></data>
            <xsl:if test="col[@field='Filter']!=''">
                <data field="filter"><xsl:value-of select="col[@field='Filter']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Folder']!=''">
                <data field="dir"><xsl:value-of select="col[@field='Folder']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Cluster Distance']!=''">
                <data field="cluster_distance"><xsl:value-of select="col[@field='Cluster Distance']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Cluster Threshold']!=''">
                <data field="cluster_threshold"><xsl:value-of select="col[@field='Cluster Threshold']"/></data>
            </xsl:if>
        </resource>

        <resource name="gis_layer_config">
            <reference field="layer_id" resource="gis_layer_shapefile">
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
            <data field="style"><xsl:value-of select="col[@field='Style']"/></data>
            <data field="enabled"><xsl:value-of select="col[@field='Enabled']"/></data>
            <data field="visible"><xsl:value-of select="col[@field='Visible']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Marker">

        <xsl:variable name="Marker" select="col[@field='Marker']/text()"/>
    
        <xsl:if test="$Marker!=''">
            <resource name="gis_marker">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Marker"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Marker"/></data>
            </resource>
        </xsl:if>
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
    
        <xsl:if test="$Symbology!=''">
            <resource name="gis_symbology">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Symbology"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Symbology"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
