<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         CMS Post - CSV Import Stylesheet

         CSV fields:
         Series...................Series Name (optional)
         Name.....................Post Name (for menu links)
         Title....................Post Title (for use in the browser-bar)
         Body.....................Post Body (HTML)
         Module...................Post Module
         Country..................optional.....Post Country
         L1.......................optional.....Post L1
         L2.......................optional.....Post L2
         L3.......................optional.....Post L3
         L4.......................optional.....Post L4
         L5.......................optional.....Post L5
         Location Name............optional.....Post Location (specific)
         Lat......................float........Latitude of most specific location
         Lon......................float........Longitude of most specific location
         Comments.................Post Comments
         Author...................Post created_by (email)
         Date.....................Post created_on (datetime)
         Attachment...............doc_document (URL to remote server to download)
         Events...................Comma-separated list of Events to tag the Post to
         Roles....................Post Roles (not yet implemented)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="Country">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Country</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="L1" match="row"
             use="concat(col[@field=$Country], '/', col[@field='L1'])"/>
    <xsl:key name="L2" match="row"
             use="concat(col[@field=$Country], '/', col[@field='L1'], '/',
                                                    col[@field='L2'])"/>
    <xsl:key name="L3" match="row"
             use="concat(col[@field=$Country], '/', col[@field='L1'], '/',
                                                    col[@field='L2'], '/',
                                                    col[@field='L3'])"/>
    <xsl:key name="L4" match="row"
             use="concat(col[@field=$Country], '/', col[@field='L1'], '/',
                                                    col[@field='L2'], '/',
                                                    col[@field='L3'], '/',
                                                    col[@field='L4'])"/>

    <xsl:key name="L5" match="row"
             use="concat(col[@field=$Country], '/', col[@field='L1'], '/',
                                                    col[@field='L2'], '/',
                                                    col[@field='L3'], '/',
                                                    col[@field='L4'], '/',
                                                    col[@field='L5'])"/>

    <xsl:key name="location" match="row"
             use="concat(col[@field=$Country], '/', col[@field='L1'], '/',
                                                    col[@field='L2'], '/',
                                                    col[@field='L3'], '/',
                                                    col[@field='L4'], '/',
                                                    col[@field='L5'], '/',
                                                    col[@field='Location Name'])"/>

    <xsl:key name="series" match="row" use="col[@field='Series']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- L1 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L1',
                                                                   concat(col[@field=$Country], '/',
                                                                          col[@field='L1']))[1])]">
                <xsl:call-template name="L1"/>
            </xsl:for-each>

            <!-- L2 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L2',
                                                                   concat(col[@field=$Country], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2']))[1])]">
                <xsl:call-template name="L2"/>
            </xsl:for-each>

            <!-- L3 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L3',
                                                                   concat(col[@field=$Country], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3']))[1])]">
                <xsl:call-template name="L3"/>
            </xsl:for-each>

            <!-- L4 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L4',
                                                                   concat(col[@field=$Country], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3'], '/',
                                                                          col[@field='L4']))[1])]">
                <xsl:call-template name="L4"/>
            </xsl:for-each>

            <!-- L5 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L5',
                                                                   concat(col[@field=$Country], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3'], '/',
                                                                          col[@field='L4'], '/',
                                                                          col[@field='L5']))[1])]">
                <xsl:call-template name="L5"/>
            </xsl:for-each>

            <!-- Location -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('location',
                                                                   concat(col[@field=$Country], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3'], '/',
                                                                          col[@field='L4'], '/',
                                                                          col[@field='L5'], '/',
                                                                          col[@field='Location Name']))[1])]">
                <xsl:call-template name="Location"/>
            </xsl:for-each>

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
        <xsl:variable name="Expired">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Expired']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="Author" select="col[@field='Author']/text()"/>
        <xsl:variable name="Date" select="col[@field='Date']/text()"/>
        <xsl:variable name="Series" select="col[@field='Series']/text()"/>
        <xsl:variable name="Name" select="col[@field='Name']/text()"/>
        <xsl:variable name="Title" select="col[@field='Title']/text()"/>
        <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>
        <xsl:variable name="Module" select="col[@field='Module']/text()"/>

        <resource name="cms_post">
            <xsl:if test="$Author!=''">
                <xsl:attribute name="created_by">
                    <xsl:value-of select="$Author"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="$Date!=''">
                <xsl:attribute name="created_on">
                    <xsl:value-of select="$Date"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="$Series!=''">
                <reference field="series_id" resource="cms_series">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Series"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="$Name!=''">
                <data field="name"><xsl:value-of select="$Name"/></data>
            </xsl:if>
            <xsl:if test="$Title!=''">
                <data field="title"><xsl:value-of select="$Title"/></data>
            </xsl:if>
            <data field="body"><xsl:value-of select="col[@field='Body']"/></data>
            <xsl:if test="$Comments!=''">
                <data field="comments"><xsl:value-of select="$Comments"/></data>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="$Expired=''">
                    <!-- Use System Default -->
                </xsl:when>
                <xsl:when test="$Expired='Y'">
                    <data field="expired" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Expired='YES'">
                    <data field="expired" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Expired='T'">
                    <data field="expired" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Expired='TRUE'">
                    <data field="expired" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Expired='N'">
                    <data field="expired" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Expired='NO'">
                    <data field="expired" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Expired='F'">
                    <data field="expired" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Expired='FALSE'">
                    <data field="expired" value="false">False</data>
                </xsl:when>
            </xsl:choose>

            <!-- Link to Module -->
            <xsl:if test="$Module!=''">
                <resource name="cms_post_module">
                    <data field="module"><xsl:value-of select="$Module"/></data>
                </resource>
            </xsl:if>

            <!-- Link to Location -->
            <xsl:call-template name="LocationReference"/>

            <!-- Attachment -->
            <xsl:if test="col[@field='Attachment']!=''">
                <resource name="doc_document">
                    <data field="file">
                        <xsl:attribute name="url">
                            <xsl:value-of select="col[@field='Attachment']"/>
                        </xsl:attribute>
                    </data>
                </resource>
            </xsl:if>

            <!-- Events -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list"><xsl:value-of select="col[@field='Events']"/></xsl:with-param>
                <xsl:with-param name="arg">event</xsl:with-param>
            </xsl:call-template>

        </resource>

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
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>

        <xsl:choose>
            <!-- Event list -->
            <xsl:when test="$arg='event'">
                <resource name="event_event_post">
                    <reference field="event_id" resource="event_event">
                        <resource name="event_event">
                            <data field="name"><xsl:value-of select="$item"/></data>
                        </resource>
                    </reference>
                </resource>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L1">
        <xsl:if test="col[@field='L1']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>

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
                <!-- If this is the import level then add the details -->
                <xsl:choose>
                    <xsl:when test="col[@field='L2'] or col[@field='L3'] or col[@field='L4'] or col[@field='L5'] or col[@field='Location Name']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                            <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L2">
        <xsl:if test="col[@field='L2']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>

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
                <!-- If this is the import level then add the details -->
                <xsl:choose>
                    <xsl:when test="col[@field='L3'] or col[@field='L4'] or col[@field='L5'] or col[@field='Location Name']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                            <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L3">
        <xsl:if test="col[@field='L3']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>

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
                <!-- If this is the import level then add the details -->
                <xsl:choose>
                    <xsl:when test="col[@field='L4'] or col[@field='L5'] or col[@field='Location Name']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                            <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L4">
        <xsl:if test="col[@field='L4']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>
            <xsl:variable name="l4" select="col[@field='L4']/text()"/>

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
                <!-- If this is the import level then add the details -->
                <xsl:choose>
                    <xsl:when test="col[@field='L5'] or col[@field='Location Name']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                            <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L5">
        <xsl:if test="col[@field='L5']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>
            <xsl:variable name="l4" select="col[@field='L4']/text()"/>
            <xsl:variable name="l5" select="col[@field='L5']/text()"/>

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
                    <xsl:value-of select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$l5"/></data>
                <data field="level"><xsl:text>L5</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L4']!=''">
                        <!-- Parent to L4 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
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
                <!-- If this is the import level then add the details -->
                <xsl:choose>
                    <xsl:when test="col[@field='Location Name']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                            <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Location">
        <xsl:if test="col[@field='Location Name']!=''">

            <xsl:variable name="l0">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Country"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>
            <xsl:variable name="l4" select="col[@field='L4']/text()"/>
            <xsl:variable name="l5" select="col[@field='L5']/text()"/>
            <xsl:variable name="location" select="col[@field='Location Name']/text()"/>

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
                    <xsl:value-of select="concat('Location/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5, '/', $location)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$location"/></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L5']!=''">
                        <!-- Parent to L5 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="col[@field='L4']!=''">
                        <!-- Parent to L4 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
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
                <!-- If this is the import level then add the details -->
                <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                    <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                    <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
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
        <xsl:variable name="location" select="col[@field='Location Name']/text()"/>

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

        <xsl:choose>
            <xsl:when test="$location!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5, '/', $location)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l5!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l4!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l3!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l2!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l1!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l0!=''">
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
