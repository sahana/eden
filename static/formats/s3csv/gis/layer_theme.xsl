<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Theme Layers - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Layer Name
         Description..........string..........Layer Description
         Date.................date............Layer Date
         Style................string..........Layer Style
         Opacity..............double..........Layer Opacity
         Folder...............string..........Layer Folder
         Config...............string..........Configuration Name
         Enabled..............boolean.........Layer Enabled in config? (SITE_DEFAULT if not-specified)
         Visible..............boolean.........Layer Enabled in config? (SITE_DEFAULT if not-specified)

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

        <xsl:variable name="Config" select="col[@field='Config']/text()"/>

        <resource name="gis_layer_theme">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <xsl:if test="col[@field='Description']!=''">
                <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Date']!=''">
                <data field="date"><xsl:value-of select="col[@field='Date']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Opacity']!=''">
                <data field="opacity"><xsl:value-of select="col[@field='Opacity']"/></data>
            </xsl:if>

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
                <xsl:if test="col[@field='Opacity']!=''">
                    <data field="opacity"><xsl:value-of select="col[@field='Opacity']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Popup Format']!=''">
                    <data field="popup_format"><xsl:value-of select="col[@field='Popup Format']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Style']!=''">
                    <data field="style"><xsl:value-of select="col[@field='Style']"/></data>
                </xsl:if>
                <xsl:choose>
                    <xsl:when test="col[@field='Cluster Threshold']!=''">
                        <data field="cluster_threshold"><xsl:value-of select="col[@field='Cluster Threshold']"/></data>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- Disable Clustering by Default -->
                        <data field="cluster_threshold">0</data>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

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
