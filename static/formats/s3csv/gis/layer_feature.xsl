<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Feature Layers - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Layer Name
         Description..........string..........Layer Description
         Marker...............string..........Style Marker Name
         GPS Marker...........string..........Style GPS Marker
         Controller...........string..........Layer Controller
         Function.............string..........Layer Function
         Filter...............string..........Layer Filter
         Aggregate............string..........Layer/Style Aggregate (define the non-aggregate style as a row in a separate style.csv)
         Popup Format.........string..........Style Popup Format
         Attributes...........comma-sep list..Layer Attributes (Fields to put in feature attributes to use for Popup Format &/or Style)
         Default..............boolean.........Layer Default
         Individual...........boolean.........Layer Individual
         Trackable............boolean.........Layer Trackable
         Site.................boolean.........Layer Site (use Site for location)
         Style................string..........Style Style
         Opacity..............string..........Style Opacity (set here to make selectStyle just remove Opacity rather than change colour)
         Folder...............string..........Layer Config Folder
         Config...............string..........Configuration Name
         Enabled..............boolean.........Layer Enabled in config? (SITE_DEFAULT if not-specified)
         Visible..............boolean.........Layer Visible in config? (SITE_DEFAULT if not-specified)
         Cluster Attribute....string..........Layer Cluster Attribute: The attribute to use for clustering
         Cluster Distance.....integer.........Style Cluster Distance: The number of pixels apart that features need to be before they are clustered (default=20)
         Cluster Threshold....integer.........Style Cluster Threshold: The minimum number of features to form a cluster (default=2, 0 to disable)
         Refresh..............integer.........Layer Refresh (Number of seconds between refreshes: 0 to disable)

    *********************************************************************** -->
    <xsl:import href="../commons.xsl"/>

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
                    <xsl:value-of select="concat('Config:', $Config)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Config"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Layer">

        <xsl:variable name="Config" select="col[@field='Config']/text()"/>
        <xsl:variable name="Marker" select="col[@field='Marker']/text()"/>
        <xsl:variable name="Attributes" select="col[@field='Attributes']/text()"/>

        <resource name="gis_layer_feature">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <xsl:if test="col[@field='Aggregate']">
                <data field="aggregate"><xsl:value-of select="col[@field='Aggregate']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Default']">
                <data field="style_default"><xsl:value-of select="col[@field='Default']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Individual']">
                <data field="individual"><xsl:value-of select="col[@field='Individual']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Trackable']">
                <data field="trackable"><xsl:value-of select="col[@field='Trackable']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Site']">
                <data field="use_site"><xsl:value-of select="col[@field='Site']"/></data>
            </xsl:if>
            <data field="controller"><xsl:value-of select="col[@field='Controller']"/></data>
            <data field="function"><xsl:value-of select="col[@field='Function']"/></data>
            <xsl:if test="col[@field='Filter']!=''">
                <data field="filter"><xsl:value-of select="col[@field='Filter']"/></data>
            </xsl:if>
            <xsl:if test="$Attributes!=''">
                <data field="attr_fields">
                    <xsl:attribute name="value">
                        <xsl:text>[</xsl:text>
                        <xsl:call-template name="listString">
                            <xsl:with-param name="list">
                                <xsl:value-of select="$Attributes"/>
                            </xsl:with-param>
                        </xsl:call-template>
                        <xsl:text>]</xsl:text>
                    </xsl:attribute>
                </data>
            </xsl:if>
            <xsl:if test="col[@field='Refresh']!=''">
                <data field="refresh"><xsl:value-of select="col[@field='Refresh']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Cluster Attribute']!=''">
                <data field="cluster_attribute"><xsl:value-of select="col[@field='Cluster Attribute']"/></data>
            </xsl:if>

            <resource name="gis_layer_config">
                <reference field="config_id" resource="gis_config">
                    <xsl:choose>
                        <xsl:when test="$Config!=''">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('Config:', $Config)"/>
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
                <xsl:if test="col[@field='Aggregate']!=''">
                    <data field="aggregate"><xsl:value-of select="col[@field='Aggregate']"/></data>
                </xsl:if>
                <xsl:if test="$Marker!=''">
                    <reference field="marker_id" resource="gis_marker">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$Marker"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
                <xsl:if test="col[@field='GPS Marker']!=''">
                    <data field="gps_marker"><xsl:value-of select="col[@field='GPS Marker']"/></data>
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
