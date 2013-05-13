<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Campaign Response Summary - CSV Import Stylesheet

         Column headers defined in this stylesheet:

         Keyword........................required.....project_campaign_keyword.name
         Quantity.......................required.....project_campaign_response_summary.value
         Date...........................optional.....project_campaign_response_summary.end_date
         Country........................optional.....gis_location.L0 Name or ISO2
         L1.............................optional.....gis_location.L1
         L2.............................optional.....gis_location.L2
         L3.............................optional.....gis_location.L3
         L4.............................optional.....gis_location.L4
         Lat............................optional.....gis_location.lat
         Lon............................optional.....gis_location.lon
         
    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="Keyword">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Keyword</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="Quantity">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Quantity</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="Date">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Date</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="Lat">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Lat</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="Lon">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Lon</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <xsl:key name="location"
             match="row"
             use="concat(col[@field='Country'],
                         col[@field='L1'],
                         col[@field='L2'],
                         col[@field='L3'],
                         col[@field='L4'],
                         col[contains(
                             document('../labels.xml')/labels/column[@name='Lat']/match/text(),
                             concat('|', @field, '|'))],
                         col[contains(
                             document('../labels.xml')/labels/column[@name='Lon']/match/text(),
                             concat('|', @field, '|'))])"/>

    <xsl:key name="keyword"
             match="row"
             use="col[contains(
                      document('../labels.xml')/labels/column[@name='Keyword']/match/text(),
                      concat('|', @field, '|'))]"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Create the Keywords -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('keyword',
                                                        col[contains(
                                                            document('../labels.xml')/labels/column[@name='Keyword']/match/text(),
                                                            concat('|', @field, '|'))])[1])]">
                <xsl:call-template name="Keyword" />
            </xsl:for-each>

            <!-- Create the Locations -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('location',
                                                        concat(col[@field='Country'],
                                                               col[@field='L1'],
                                                               col[@field='L2'],
                                                               col[@field='L3'],
                                                               col[@field='L4'],
                                                               col[contains(
                                                                   document('../labels.xml')/labels/column[@name='Lat']/match/text(),
                                                                   concat('|', @field, '|'))],
                                                               col[contains(
                                                                   document('../labels.xml')/labels/column[@name='Lon']/match/text(),
                                                                   concat('|', @field, '|'))]))[1])]">
                <xsl:call-template name="Locations"/>
            </xsl:for-each>

            <!-- Create the Response Summary records -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Response Summary Record -->
    <xsl:template match="row">
        <xsl:variable name="quantity">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Quantity"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="date">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Date"/>
            </xsl:call-template>
        </xsl:variable>

         <xsl:variable name="keyword">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Keyword"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="lat">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lat"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="lon">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lon"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:if test="$quantity!=''">
            <resource name="project_campaign_response_summary">
                <data field="value"><xsl:value-of select="$quantity"/></data>
                <data field="end_date"><xsl:value-of select="$date"/></data>

                <!-- Link to Keyword -->
                <reference field="parameter_id" resource="project_campaign_keyword">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('campaign_keyword/',$keyword)"/>
                    </xsl:attribute>
                </reference>

                <!-- Link to Location -->
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat(col[@field='Country'],
                                                     col[@field='L1'],
                                                     col[@field='L2'],
                                                     col[@field='L3'],
                                                     col[@field='L4'],
                                                     $lat,
                                                     $lon)"/>
                    </xsl:attribute>
                </reference>

            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Keyword">

        <xsl:variable name="name">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Keyword"/>
            </xsl:call-template>
        </xsl:variable>

        <resource name="project_campaign_keyword">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('campaign_keyword/',$name)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$name"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Locations">

        <!--<xsl:variable name="StationName" select="col[@field='Name']/text()"/>-->
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>

        <xsl:variable name="lat">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lat"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="lon">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lon"/>
            </xsl:call-template>
        </xsl:variable>

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
                    <xsl:value-of select="concat('L1',$l1)"/>
                </xsl:attribute>
                <reference field="parent" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
                <data field="name"><xsl:value-of select="$l1"/></data>
                <data field="level"><xsl:text>L1</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- L2 Location -->
        <xsl:if test="$l2!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L2',$l2)"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1',$l1)"/>
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
            </resource>
        </xsl:if>

        <!-- L3 Location -->
        <xsl:if test="$l3!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L3',$l3)"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2',$l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1',$l1)"/>
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
            </resource>
        </xsl:if>

        <!-- L4 Location -->
        <xsl:if test="$l4!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L4',$l4)"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l3!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3',$l3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2',$l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1',$l1)"/>
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
            </resource>
        </xsl:if>

        <!-- Base Station Location -->
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat(col[@field='Country'],
                                             col[@field='L1'],
                                             col[@field='L2'],
                                             col[@field='L3'],
                                             col[@field='L4'],
                                             $lat,
                                             $lon)"/>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="$l4!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L4',$l4)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l3!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L3',$l3)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l2!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L2',$l2)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l1!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L1',$l1)"/>
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

            <!--<data field="name"><xsl:value-of select="$StationName"/></data>-->
            <data field="lat"><xsl:value-of select="$lat"/></data>
            <data field="lon"><xsl:value-of select="$lon"/></data>
        </resource>

    </xsl:template>

</xsl:stylesheet>
