<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         KML Layers - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Layer Name
         Description..........string..........Layer Description
         URL..................string..........Layer URL
         Symbology............string..........Symbology Name
         Marker...............string..........Layer Symbology Marker Name
         Folder...............string..........Layer Folder
         Title................string..........Layer Title
         Body.................string..........Layer Body
         Config...............string..........Configuration Name
         Enabled..............boolean.........Layer Enabled in config? (SITE_DEFAULT if not-specified)
         Visible..............boolean.........Layer Visible in config? (SITE_DEFAULT if not-specified)

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
    <xsl:key name="symbologies" match="row" use="col[@field='Symbology']/text()"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Configs -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('configs',
                                                                   col[@field='Config'])[1])]">
                <xsl:call-template name="Config"/>
            </xsl:for-each>

            <!-- KML Layers -->
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

        <xsl:variable name="Layer" select="col[@field='Name']/text()"/>

        <resource name="gis_layer_symbology">
            <reference field="layer_id" resource="gis_layer_kml">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Layer"/>
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

    <xsl:template name="Layer">

        <xsl:variable name="Layer" select="col[@field='Name']/text()"/>
        <xsl:variable name="Config" select="col[@field='Config']/text()"/>

        <resource name="gis_layer_kml">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Layer"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Layer"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <data field="url"><xsl:value-of select="col[@field='URL']"/></data>
            <data field="dir"><xsl:value-of select="col[@field='Folder']"/></data>
            <xsl:if test="col[@field='Title'] != ''">
                <data field="title"><xsl:value-of select="col[@field='Title']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Body'] != ''">
                <data field="body"><xsl:value-of select="col[@field='Body']"/></data>
            </xsl:if>
        </resource>

        <resource name="gis_layer_config">
            <reference field="layer_id" resource="gis_layer_kml">
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
