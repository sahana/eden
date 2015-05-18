<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Styles - CSV Import Stylesheet

         CSV column...........Format..........Content

         Config...............string..........Configuration Name (required only if want to restrict to a specific config / override default config)
         Layer................string..........Layer Name
         Layer Type...........string..........Layer Type (only needed if not gis_layer_feature)
         Record...............string..........Layer Record. @ToDo: make this useful by providing a way to look this up (hard-coded record IDs aren't useful)
         Aggregate............string..........Style Aggregate
         Marker...............string..........Style Marker Name
         GPS Marker...........string..........Style GPS Marker
         Popup Format.........string..........Style Popup Format
         Style................string..........Style Style
         Opacity..............string..........Style Opacity (set here to make selectStyle just remove Opacity rather than change colour)
         Cluster Distance.....integer.........Style Cluster Distance: The number of pixels apart that features need to be before they are clustered (default=20)
         Cluster Threshold....integer.........Style Cluster Threshold: The minimum number of features to form a cluster (default=2, 0 to disable)

    *********************************************************************** -->
    <xsl:import href="../commons.xsl"/>

    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="configs" match="row" use="col[@field='Config']/text()"/>
    <xsl:key name="layers" match="row"
             use="concat(col[@field='Layer'], '/', col[@field='Layer Type'])"/>
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
                                                                   concat(col[@field='Layer'], '/',
                                                                          col[@field='Layer Type']))[1])]">
                <xsl:call-template name="Layer"/>
            </xsl:for-each>

            <!-- Markers -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('markers',
                                                                   col[@field='Marker'])[1])]">
                <xsl:call-template name="Marker"/>
            </xsl:for-each>

            <!-- Styles -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Config" select="col[@field='Config']/text()"/>
        <xsl:variable name="Layer" select="col[@field='Layer']/text()"/>
        <xsl:variable name="Marker" select="col[@field='Marker']/text()"/>

        <resource name="gis_style">
            <xsl:if test="$Config!=''">
                <reference field="config_id" resource="gis_config">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Config"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="$Layer!=''">
                <xsl:variable name="LayerType" select="col[@field='Layer Type']/text()"/>
                <xsl:variable name="resourcename">
                    <xsl:choose>
                        <xsl:when test="$LayerType!=''">
                            <xsl:value-of select="$LayerType"/>
                        </xsl:when>
                        <xsl:otherwise>gis_layer_feature</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <reference field="layer_id">
                    <xsl:attribute name="resource">
                        <xsl:value-of select="$resourcename"/>
                    </xsl:attribute>
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($LayerType, $Layer)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="col[@field='Record']!=''">
                <data field="record"><xsl:value-of select="col[@field='Record']"/></data>
            </xsl:if>
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

        <xsl:variable name="Layer" select="col[@field='Layer']/text()"/>

        <xsl:if test="$Layer!=''">
            <xsl:variable name="LayerType" select="col[@field='Layer Type']/text()"/>
            <xsl:variable name="resourcename">
                <xsl:choose>
                    <xsl:when test="$LayerType!=''">
                        <xsl:value-of select="$LayerType"/>
                    </xsl:when>
                    <xsl:otherwise>gis_layer_feature</xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <resource>
                <xsl:attribute name="name">
                    <xsl:value-of select="$resourcename"/>
                </xsl:attribute>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($LayerType, $Layer)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Layer"/></data>
            </resource>
        </xsl:if>

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
