<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         GeoRSS Layers - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Layer Name
         Description..........string..........Layer Description
         URL..................string..........Layer URL
         Marker...............string..........Layer Symbology Marker Name
         Folder...............string..........Layer Folder
         Image................string..........Layer Image
         Config...............string..........Configuration Name
         Enabled..............boolean.........Layer Enabled in config? (SITE_DEFAULT if not-specified)
         Visible..............boolean.........Layer Visible in config? (SITE_DEFAULT if not-specified)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="configs" match="row" use="col[@field='Config']/text()"/>
    <xsl:key name="layers" match="row" use="concat(col[@field='Config'], '/',
                                                   col[@field='Name'])"/>
    <xsl:key name="markers" match="row" use="col[@field='Marker']/text()"/>

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
                                                                   concat(col[@field='Config'], '/',
                                                                          col[@field='Name']))[1])]">
                <xsl:call-template name="Layer"/>
            </xsl:for-each>

            <!-- Markers -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('markers',
                                                                   col[@field='Marker'])[1])]">
                <xsl:call-template name="Marker"/>
            </xsl:for-each>

        </s3xml>
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

        <xsl:variable name="Config" select="col[@field='Config']/text()"/>
        <xsl:variable name="Marker" select="col[@field='Marker']/text()"/>

        <resource name="gis_layer_georss">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <data field="url"><xsl:value-of select="col[@field='URL']"/></data>
            <data field="image"><xsl:value-of select="col[@field='Image']"/></data>

            <resource name="gis_layer_config">
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
                <xsl:if test="col[@field='Folder']!=''">
                    <data field="dir"><xsl:value-of select="col[@field='Folder']"/></data>
                </xsl:if>
                <data field="enabled"><xsl:value-of select="col[@field='Enabled']"/></data>
                <data field="visible"><xsl:value-of select="col[@field='Visible']"/></data>
            </resource>

            <resource name="gis_style">
                <!-- @ToDo: Allow restricting the style to a specific Config
                <xsl:if test="$Config!=''">
                    <reference field="config_id" resource="gis_config">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$Config"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if> -->
                <xsl:if test="$Marker!=''">
                    <reference field="marker_id" resource="gis_marker">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$Marker"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
                <xsl:if test="col[@field='Opacity']!=''">
                    <data field="opacity"><xsl:value-of select="col[@field='Opacity']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Popup Format']!=''">
                    <data field="popup_format"><xsl:value-of select="col[@field='Popup Format']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Style']!=''">
                    <data field="style"><xsl:value-of select="col[@field='Style']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Cluster Distance']!=''">
                    <data field="cluster_distance"><xsl:value-of select="col[@field='Cluster Distance']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Cluster Threshold']!=''">
                    <data field="cluster_threshold"><xsl:value-of select="col[@field='Cluster Threshold']"/></data>
                </xsl:if>
            </resource>

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

</xsl:stylesheet>
