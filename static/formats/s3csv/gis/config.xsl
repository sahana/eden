<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         GIS Configurations - CSV Import Stylesheet

         CSV column...........Format..........Content

         UID..................string..........gis_config.uuid (needed for SITE_DEFAULT)
         Name.................string..........gis_config.name
         OU...................string..........gis_config.pe_id
         OU Type..............string..........gis_config.pe_type (currently only Orgs supported, but easy to extend)
         Region Country.......string..........gis_config.region_location_id.L0
         Region L1............string..........gis_config.region_location_id.L1
         Region L2............string..........gis_config.region_location_id.L2
         Region L3............string..........gis_config.region_location_id.L3
         Region L4............string..........gis_config.region_location_id.L4
         Default Country......string..........gis_config.default_location_id.L0
         Default L1...........string..........gis_config.default_location_id.L1
         Default L2...........string..........gis_config.default_location_id.L2
         Default L3...........string..........gis_config.default_location_id.L3
         Default L4...........string..........gis_config.default_location_id.L4
         Zoom.................integer.........gis_config.zoom
         Lat..................float...........gis_config.lat
         Lon..................float...........gis_config.lon
         Projection...........integer.........gis_config.projection.epsg
         Symbology............string..........gis_config.symbology_id
         LatMin...............float...........gis_config.lat_min
         LatMax...............float...........gis_config.lat_max
         LonMin...............float...........gis_config.lon_min
         LonMax...............float...........gis_config.lon_max
         WMS Browser..........float...........gis_config.wmsbrowser_url
         

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="projections" match="row" use="col[@field='Projection']/text()"/>
    <xsl:key name="symbologies" match="row" use="col[@field='Symbology']/text()"/>
    <xsl:key name="ous" match="row"
             use="concat(col[@field='OU Type'], '/', col[@field='OU'])"/>

    <xsl:key name="Default L1" match="row"
             use="concat(col[@field='Default Country'], '/', col[@field='Default L1'])"/>
    <xsl:key name="Default L2" match="row"
             use="concat(col[@field='Default Country'], '/', col[@field='Default L1'], '/',
                                                             col[@field='Default L2'])"/>
    <xsl:key name="Default L3" match="row"
             use="concat(col[@field='Default Country'], '/', col[@field='Default L1'], '/',
                                                             col[@field='Default L2'], '/',
                                                             col[@field='Default L3'])"/>
    <xsl:key name="Default L4" match="row"
             use="concat(col[@field='Default Country'], '/', col[@field='Default L1'], '/',
                                                             col[@field='Default L2'], '/',
                                                             col[@field='Default L3'], '/',
                                                             col[@field='Default L4'])"/>

    <xsl:key name="Region L1" match="row"
             use="concat(col[@field='Region Country'], '/', col[@field='Region L1'])"/>
    <xsl:key name="Region L2" match="row"
             use="concat(col[@field='Region Country'], '/', col[@field='Region L1'], '/',
                                                            col[@field='Region L2'])"/>
    <xsl:key name="Region L3" match="row"
             use="concat(col[@field='Region Country'], '/', col[@field='Region L1'], '/',
                                                            col[@field='Region L2'], '/',
                                                            col[@field='Region L3'])"/>
    <xsl:key name="Region L4" match="row"
             use="concat(col[@field='Region Country'], '/', col[@field='Region L1'], '/',
                                                            col[@field='Region L2'], '/',
                                                            col[@field='Region L3'], '/',
                                                            col[@field='Region L4'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- L1 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('Default L1',
                                                                   concat(col[@field='Default Country'], '/',
                                                                          col[@field='Default L1']))[1])]">
                <xsl:call-template name="L1">
                    <xsl:with-param name="prefix" select="Default"/>
                </xsl:call-template>
            </xsl:for-each>

            <xsl:for-each select="//row[generate-id(.)=generate-id(key('Region L1',
                                                                   concat(col[@field='Region Country'], '/',
                                                                          col[@field='Region L1']))[1])]">
                <xsl:call-template name="L1">
                    <xsl:with-param name="prefix" select="Region"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- L2 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('Default L2',
                                                                   concat(col[@field='Default Country'], '/',
                                                                          col[@field='Default L1'], '/',
                                                                          col[@field='Default L2']))[1])]">
                <xsl:call-template name="L2">
                    <xsl:with-param name="prefix" select="Default"/>
                </xsl:call-template>
            </xsl:for-each>

            <xsl:for-each select="//row[generate-id(.)=generate-id(key('Region L2',
                                                                   concat(col[@field='Region Country'], '/',
                                                                          col[@field='Region L1'], '/',
                                                                          col[@field='Region L2']))[1])]">
                <xsl:call-template name="L2">
                    <xsl:with-param name="prefix" select="Region"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- L3 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('Default L3',
                                                                   concat(col[@field='Default Country'], '/',
                                                                          col[@field='Default L1'], '/',
                                                                          col[@field='Default L2'], '/',
                                                                          col[@field='Default L3']))[1])]">
                <xsl:call-template name="L3">
                    <xsl:with-param name="prefix" select="Default"/>
                </xsl:call-template>
            </xsl:for-each>

            <xsl:for-each select="//row[generate-id(.)=generate-id(key('Region L3',
                                                                   concat(col[@field='Region Country'], '/',
                                                                          col[@field='Region L1'], '/',
                                                                          col[@field='Region L2'], '/',
                                                                          col[@field='Region L3']))[1])]">
                <xsl:call-template name="L3">
                    <xsl:with-param name="prefix" select="Region"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- L4 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('Default L4',
                                                                   concat(col[@field='Default Country'], '/',
                                                                          col[@field='Default L1'], '/',
                                                                          col[@field='Default L2'], '/',
                                                                          col[@field='Default L3'], '/',
                                                                          col[@field='Default L4']))[1])]">
                <xsl:call-template name="L4">
                    <xsl:with-param name="prefix" select="Default"/>
                </xsl:call-template>
            </xsl:for-each>

            <xsl:for-each select="//row[generate-id(.)=generate-id(key('Region L4',
                                                                   concat(col[@field='Region Country'], '/',
                                                                          col[@field='Region L1'], '/',
                                                                          col[@field='Region L2'], '/',
                                                                          col[@field='Region L3'], '/',
                                                                          col[@field='Region L4']))[1])]">
                <xsl:call-template name="L4">
                    <xsl:with-param name="prefix" select="Region"/>
                </xsl:call-template>
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

            <!-- OUs -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('ous',
                                                        concat(col[@field='OU Type'], '/',
                                                               col[@field='OU']))[1])]">
                <xsl:call-template name="OU"/>
            </xsl:for-each>

            <!-- Configs -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="ou" select="col[@field='OU']/text()"/>
        <xsl:variable name="ou_type" select="col[@field='OU Type']/text()"/>
        <xsl:variable name="Projection" select="col[@field='Projection']/text()"/>
        <xsl:variable name="Symbology" select="col[@field='Symbology']/text()"/>
    
        <resource name="gis_config">
            <xsl:if test="col[@field='UUID']!=''">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="col[@field='UUID']"/>
                </xsl:attribute>
            </xsl:if>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="zoom"><xsl:value-of select="col[@field='Zoom']"/></data>
            <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
            <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
            <data field="lat_min"><xsl:value-of select="col[@field='LatMin']"/></data>
            <data field="lon_min"><xsl:value-of select="col[@field='LonMin']"/></data>
            <data field="lat_max"><xsl:value-of select="col[@field='LatMax']"/></data>
            <data field="lon_max"><xsl:value-of select="col[@field='LonMax']"/></data>
            <xsl:if test="col[@field='WMS Browser']!=''">
                <data field="wmsbrowser_url"><xsl:value-of select="col[@field='WMS Browser']"/></data>
            </xsl:if>

            <reference field="projection_id" resource="gis_projection">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Projection"/>
                </xsl:attribute>
            </reference>
            <reference field="symbology_id" resource="gis_symbology">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Symbology"/>
                </xsl:attribute>
            </reference>

            <xsl:call-template name="LocationReference">
                <xsl:with-param name="prefix" select="Region"/>
            </xsl:call-template>
            <xsl:call-template name="LocationReference">
                <xsl:with-param name="prefix" select="Default"/>
            </xsl:call-template>

            <xsl:if test="$ou!=''">
                <xsl:choose>
                    <xsl:when test="$ou_type='organisation' or 
                                    $ou_type='organization'">
                        <reference field="pe_id" resource="org_organisation">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($ou_type, $ou)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </xsl:if>
        </resource>
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
    
        <resource name="gis_symbology">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Symbology"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Symbology"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="OU">

        <xsl:variable name="ou" select="col[@field='OU']/text()"/>
        <xsl:variable name="ou_type" select="col[@field='OU Type']/text()"/>
    
        <xsl:choose>
            <xsl:when test="$ou_type='organisation' or 
                            $ou_type='organization'">
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                         <xsl:value-of select="concat($ou_type, $ou)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$ou"/></data>
                </resource>
            </xsl:when>
        </xsl:choose>
            
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L1">
        <xsl:param name="prefix"/>
        <xsl:variable name="L1">
            <xsl:value-of select="concat($prefix, ' L1')"/>
        </xsl:variable>

        <xsl:if test="col[@field=$L1]!=''">

            <xsl:variable name="Country">
                <xsl:value-of select="concat($prefix, ' Country')"/>
            </xsl:variable>

            <xsl:variable name="l0" select="col[@field=$Country]/text()"/>
            <xsl:variable name="l1" select="col[@field=$L1]/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="uppercase">
                            <xsl:with-param name="string">
                               <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l1"/></data>
                <data field="level"><xsl:text>L1</xsl:text></data>
                <!-- Parent to Country -->
                <xsl:if test="$countrycode!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$country"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L2">
        <xsl:param name="prefix"/>
        <xsl:variable name="L2">
            <xsl:value-of select="concat($prefix, ' L2')"/>
        </xsl:variable>

        <xsl:if test="col[@field=$L2]!=''">

            <xsl:variable name="Country">
                <xsl:value-of select="concat($prefix, ' Country')"/>
            </xsl:variable>
            <xsl:variable name="L1">
                <xsl:value-of select="concat($prefix, ' L1')"/>
            </xsl:variable>

            <xsl:variable name="l0" select="col[@field=$Country]/text()"/>
            <xsl:variable name="l1" select="col[@field=$L1]/text()"/>
            <xsl:variable name="l2" select="col[@field=$L2]/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="uppercase">
                            <xsl:with-param name="string">
                               <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l2"/></data>
                <data field="level"><xsl:text>L2</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L3">
        <xsl:param name="prefix"/>
        <xsl:variable name="L3">
            <xsl:value-of select="concat($prefix, ' L3')"/>
        </xsl:variable>

        <xsl:if test="col[@field=$L3]!=''">

            <xsl:variable name="Country">
                <xsl:value-of select="concat($prefix, ' Country')"/>
            </xsl:variable>
            <xsl:variable name="L1">
                <xsl:value-of select="concat($prefix, ' L1')"/>
            </xsl:variable>
            <xsl:variable name="L2">
                <xsl:value-of select="concat($prefix, ' L2')"/>
            </xsl:variable>

            <xsl:variable name="l0" select="col[@field=$Country]/text()"/>
            <xsl:variable name="l1" select="col[@field=$L1]/text()"/>
            <xsl:variable name="l2" select="col[@field=$L2]/text()"/>
            <xsl:variable name="l3" select="col[@field=$L3]/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$l0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l3"/></data>
                <data field="level"><xsl:text>L3</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L4">
        <xsl:param name="prefix"/>
        <xsl:variable name="L4">
            <xsl:value-of select="concat($prefix, ' L4')"/>
        </xsl:variable>

        <xsl:if test="col[@field=$L4]!=''">

            <xsl:variable name="Country">
                <xsl:value-of select="concat($prefix, ' Country')"/>
            </xsl:variable>
            <xsl:variable name="L1">
                <xsl:value-of select="concat($prefix, ' L1')"/>
            </xsl:variable>
            <xsl:variable name="L2">
                <xsl:value-of select="concat($prefix, ' L2')"/>
            </xsl:variable>
            <xsl:variable name="L3">
                <xsl:value-of select="concat($prefix, ' L3')"/>
            </xsl:variable>

            <xsl:variable name="l0" select="col[@field=$Country]/text()"/>
            <xsl:variable name="l1" select="col[@field=$L1]/text()"/>
            <xsl:variable name="l2" select="col[@field=$L2]/text()"/>
            <xsl:variable name="l3" select="col[@field=$L3]/text()"/>
            <xsl:variable name="l4" select="col[@field=$L4]/text()"/>

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($l0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$l0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$l0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l4"/></data>
                <data field="level"><xsl:text>L4</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L3']!=''">
                        <!-- Parent to L3 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L2']!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L1']!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LocationReference">
        <xsl:param name="prefix"/>
        <xsl:variable name="Country">
            <xsl:value-of select="concat($prefix, ' Country')"/>
        </xsl:variable>
        <xsl:variable name="L1">
            <xsl:value-of select="concat($prefix, ' L1')"/>
        </xsl:variable>
        <xsl:variable name="L2">
            <xsl:value-of select="concat($prefix, ' L2')"/>
        </xsl:variable>
        <xsl:variable name="L3">
            <xsl:value-of select="concat($prefix, ' L3')"/>
        </xsl:variable>
        <xsl:variable name="L4">
            <xsl:value-of select="concat($prefix, ' L4')"/>
        </xsl:variable>

        <xsl:variable name="l0" select="col[@field=$Country]/text()"/>
        <xsl:variable name="l1" select="col[@field=$L1]/text()"/>
        <xsl:variable name="l2" select="col[@field=$L2]/text()"/>
        <xsl:variable name="l3" select="col[@field=$L3]/text()"/>
        <xsl:variable name="l4" select="col[@field=$L4]/text()"/>
        <!-- Country Code = UUID of the L0 Location -->
        <xsl:variable name="countrycode">
            <xsl:choose>
                <xsl:when test="string-length($l0)!=2">
                    <xsl:call-template name="countryname2iso">
                        <xsl:with-param name="country">
                            <xsl:value-of select="$l0"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="uppercase">
                        <xsl:with-param name="string">
                           <xsl:value-of select="$l0"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="l1id" select="concat('L1/', $countrycode, '/', $l1)"/>
        <xsl:variable name="l2id" select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
        <xsl:variable name="l3id" select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
        <xsl:variable name="l4id" select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>

        <xsl:variable name="field">
            <xsl:choose>
                <xsl:when test="$prefix='Region'">
                    <xsl:value-of select="region_location_id"/>
                </xsl:when>
                <xsl:when test="$prefix='Default'">
                    <xsl:value-of select="default_location_id"/>
                </xsl:when>
            </xsl:choose>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="$l4!=''">
                <reference field="$field" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l4id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l3!=''">
                <reference field="$field" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l3id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l2!=''">
                <reference field="$field" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l2id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l1!=''">
                <reference field="$field" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l1id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l0!=''">
                <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>
                <reference field="$field" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
