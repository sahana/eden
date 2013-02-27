<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         CMS Post - CSV Import Stylesheet

         CSV fields:
         Series...................Series Name (optional)
         Name.....................Post Name (for menu links)
         Name.....................Post Title (for use in the browser-bar)
         Body.....................Post Body (HTML)
         Module...................Post Module
         Country..................optional.....Post Country
         L1.......................optional.....Post L1
         L2.......................optional.....Post L2
         L3.......................optional.....Post L3
         L4.......................optional.....Post L4
         L5.......................optional.....Post L5
         Lat......................float........Latitude of the most local location
         Lon......................float........Longitude of the most local location
         Comments.................Post Comments
         Roles....................Post Roles (not yet implemented)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:key name="series" match="row" use="col[@field='Series']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Series -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('series',
                                                                   col[@field='Series'])[1])]">
                <xsl:call-template name="Series"/>
            </xsl:for-each>

            <!-- Posts -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Series" select="col[@field='Series']/text()"/>
        <xsl:variable name="Module" select="col[@field='Module']/text()"/>

        <resource name="cms_post">
            <xsl:if test="$Series!=''">
                <reference field="series_id" resource="cms_series">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Series"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="$Module!=''">
                <resource name="cms_post_module">
                    <data field="module"><xsl:value-of select="$Module"/></data>
                </resource>
            </xsl:if>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="title"><xsl:value-of select="col[@field='Title']"/></data>
            <data field="body"><xsl:value-of select="col[@field='Body']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

            <!-- Link to Location -->
            <xsl:call-template name="LocationReference"/>

        </resource>

        <!-- Locations -->
        <xsl:call-template name="Locations"/>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Series">
        <xsl:variable name="Series" select="col[@field='Series']/text()"/>

        <resource name="cms_series">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Series"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Series"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Locations">

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="l5" select="col[@field='L5']/text()"/>

        <xsl:variable name="l1id" select="concat('L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('L4: ', $l4)"/>
        <xsl:variable name="l5id" select="concat('L5: ', $l5)"/>

        <xsl:variable name="lat" select="col[@field='Lat']"/>
        <xsl:variable name="lon" select="col[@field='Lon']"/>

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

        <!-- L1 Location -->
        <xsl:if test="$l1!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l1id"/>
                </xsl:attribute>
                <reference field="parent" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
                <data field="name"><xsl:value-of select="$l1"/></data>
                <data field="level"><xsl:text>L1</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L2'] or col[@field='L3'] or col[@field='L4']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="$lat"/></data>
                            <data field="lon"><xsl:value-of select="$lon"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>
        </xsl:if>

        <!-- L2 Location -->
        <xsl:if test="$l2!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l2id"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:otherwise>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:otherwise>
                </xsl:choose>
                <data field="name"><xsl:value-of select="$l2"/></data>
                <data field="level"><xsl:text>L2</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L3'] or col[@field='L4']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="$lat"/></data>
                            <data field="lon"><xsl:value-of select="$lon"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>
        </xsl:if>

        <!-- L3 Location -->
        <xsl:if test="$l3!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l3id"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l2id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:otherwise>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:otherwise>
                </xsl:choose>
                <data field="name"><xsl:value-of select="$l3"/></data>
                <data field="level"><xsl:text>L3</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L4']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="$lat"/></data>
                            <data field="lon"><xsl:value-of select="$lon"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>
        </xsl:if>

        <!-- L4 Location -->
        <xsl:if test="$l4!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l4id"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l3!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l3id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l2id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:otherwise>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:otherwise>
                </xsl:choose>
                <data field="name"><xsl:value-of select="$l4"/></data>
                <data field="level"><xsl:text>L4</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L5']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="$lat"/></data>
                            <data field="lon"><xsl:value-of select="$lon"/></data>
                        </xsl:if>
                     </xsl:otherwise>
                </xsl:choose>
            </resource>
        </xsl:if>

        <!-- L5 Location -->
        <xsl:if test="$l5!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l5id"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l4!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l4id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l3!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l3id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l2id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:otherwise>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:otherwise>
                </xsl:choose>
                <data field="name"><xsl:value-of select="$l5"/></data>
                <data field="level"><xsl:text>L5</xsl:text></data>
                <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                    <data field="lat"><xsl:value-of select="$lat"/></data>
                    <data field="lon"><xsl:value-of select="$lon"/></data>
                </xsl:if>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LocationReference">

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="l5" select="col[@field='L5']/text()"/>

        <xsl:variable name="l1id" select="concat('L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('L4: ', $l4)"/>
        <xsl:variable name="l5id" select="concat('L5: ', $l5)"/>

        <xsl:choose>
            <xsl:when test="$l5!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l5id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l4!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l4id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l3!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l3id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l2!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l2id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l1!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l1id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l0!=''">
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
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
