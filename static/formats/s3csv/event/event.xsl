<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Events - CSV Import Stylesheet

         CSV fields:
         Name OR Reference.......event_event.name
         Type....................event_event.event_type_id or event_event_type.parent
         SubType.................event_event.event_type_id or event_event_type.parent
         SubSubType..............event_event.event_type_id
         Description.............event_event.comments
         Exercise................event_event.exercise
         Start Date..............event_event.start_date
         End Date................event_event.end_date
         Closed..................event_event.closed
         Country.................optional.....event_event_location.Country
         L1......................optional.....event_event_location.L1
         L2......................optional.....event_event_location.L2
         L3......................optional.....event_event_location.L3
         L4......................optional.....event_event_location.L4 (not commonly-used)
         L5......................optional.....event_event_location.L5 (not commonly-used)
         Impact:XX...............Impact Type,Value (Impact Type = XX in column name, value = cell in row)
         KV:XX...................Key,Value (Key = XX in column name, value = cell in row)

        @ToDo: Allow linking an Event to more than a single Location

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:variable name="EventTypePrefix" select="'EventType:'"/>

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
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/', 
                         col[@field='L1'])"/>
    <xsl:key name="L2" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/', 
                         col[@field='L1'], '/',
                         col[@field='L2'])"/>
    <xsl:key name="L3" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/', 
                         col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'])"/>
    <xsl:key name="L4" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/',
                         col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'], '/',
                         col[@field='L4'])"/>

    <xsl:key name="L5" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/',
                         col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'], '/',
                         col[@field='L4'], '/',
                         col[@field='L5'])"/>

    <xsl:key name="type" match="row" use="concat(col[@field='Type'], '/',
                                                 col[@field='SubType'], '/',
                                                 col[@field='SubSubType'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- L1 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L1',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1']))[1])]">
                <xsl:call-template name="L1"/>
            </xsl:for-each>

            <!-- L2 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L2',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2']))[1])]">
                <xsl:call-template name="L2"/>
            </xsl:for-each>

            <!-- L3 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L3',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3']))[1])]">
                <xsl:call-template name="L3"/>
            </xsl:for-each>

            <!-- L4 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L4',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3'], '/',
                                                                          col[@field='L4']))[1])]">
                <xsl:call-template name="L4"/>
            </xsl:for-each>

            <!-- L5 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('L5',
                                                                   concat(col[contains(
                                                                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                                                                              concat('|', @field, '|'))], '/',
                                                                          col[@field='L1'], '/',
                                                                          col[@field='L2'], '/',
                                                                          col[@field='L3'], '/',
                                                                          col[@field='L4'], '/',
                                                                          col[@field='L5']))[1])]">
                <xsl:call-template name="L5"/>
            </xsl:for-each>

            <!-- Event Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('type',
                                                                   concat(col[@field='Type'], '/',
                                                                          col[@field='SubType'], '/',
                                                                          col[@field='SubSubType']))[1])]">
                <xsl:call-template name="EventType">
                    <xsl:with-param name="Type">
                         <xsl:value-of select="col[@field='Type']"/>
                    </xsl:with-param>
                    <xsl:with-param name="SubType">
                         <xsl:value-of select="col[@field='SubType']"/>
                    </xsl:with-param>
                    <xsl:with-param name="SubSubType">
                         <xsl:value-of select="col[@field='SubSubType']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Impact Types -->
            <xsl:for-each select="//row[1]/col[starts-with(@field, 'Impact')]">
                <xsl:call-template name="ImpactType"/>
            </xsl:for-each>

            <!-- Events -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Exercise">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Exercise']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Closed">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Closed']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="EventName">
            <xsl:if test="col[@field='Name']!=''">
                <xsl:value-of select="col[@field='Name']"/>
            </xsl:if>
            <xsl:if test="col[@field='Reference']!=''">
                <xsl:value-of select="col[@field='Reference']"/>
            </xsl:if>
        </xsl:variable>
        <xsl:variable name="Type">
            <xsl:value-of select="col[@field='Type']"/>
        </xsl:variable>
        <xsl:variable name="SubType">
            <xsl:value-of select="col[@field='SubType']"/>
        </xsl:variable>
        <xsl:variable name="SubSubType">
            <xsl:value-of select="col[@field='SubSubType']"/>
        </xsl:variable>

        <!-- Event -->
        <resource name="event_event">
            <data field="name"><xsl:value-of select="$EventName"/></data>
            <data field="start_date"><xsl:value-of select="col[@field='Start Date']"/></data>
            <xsl:if test="col[@field='End Date']!=''">
                <data field="end_date"><xsl:value-of select="col[@field='End Date']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Description']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Description']"/></data>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="$Exercise='Y'">
                    <data field="exercise" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Exercise='YES'">
                    <data field="exercise" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Exercise='T'">
                    <data field="exercise" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Exercise='TRUE'">
                    <data field="exercise" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Exercise='N'">
                    <data field="exercise" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Exercise='NO'">
                    <data field="exercise" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Exercise='F'">
                    <data field="exercise" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Exercise='FALSE'">
                    <data field="exercise" value="false">False</data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Use System Default -->
                </xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="$Closed='Y'">
                    <data field="closed" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Closed='YES'">
                    <data field="closed" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Closed='T'">
                    <data field="closed" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Closed='TRUE'">
                    <data field="closed" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Closed='N'">
                    <data field="closed" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Closed='NO'">
                    <data field="closed" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Closed='F'">
                    <data field="closed" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Closed='FALSE'">
                    <data field="closed" value="false">False</data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Use System Default -->
                </xsl:otherwise>
            </xsl:choose>

            <!-- Link to Event Type -->
            <xsl:if test="$Type!=''">
                <reference field="event_type_id" resource="event_event_type">
                    <xsl:attribute name="tuid">
                        <xsl:choose>
                            <xsl:when test="$SubSubType!=''">
                                <!-- Hierarchical Type with 3 levels -->
                                <xsl:value-of select="concat($EventTypePrefix, $Type, '/', $SubType, '/', $SubSubType)"/>
                            </xsl:when>
                            <xsl:when test="$SubType!=''">
                                <!-- Hierarchical Type with 2 levels -->
                                <xsl:value-of select="concat($EventTypePrefix, $Type, '/', $SubType)"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <!-- Simple Type -->
                                <xsl:value-of select="concat($EventTypePrefix, $Type)"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Link to Location(s) -->
            <xsl:variable name="l0" select="col[@field='Country']/text()"/>
            <xsl:variable name="l1" select="col[@field='L1']/text()"/>
            <xsl:variable name="l2" select="col[@field='L2']/text()"/>
            <xsl:variable name="l3" select="col[@field='L3']/text()"/>
            <xsl:variable name="l4" select="col[@field='L4']/text()"/>
            <xsl:variable name="l5" select="col[@field='L5']/text()"/>

            <xsl:if test="col[contains(
                              document('../labels.xml')/labels/column[@name='Country']/match/text(),
                              concat('|', @field, '|'))]!=''">
                <resource name="event_event_location">
                    <xsl:call-template name="LocationReference">
                        <xsl:with-param name="l0">
                            <xsl:value-of select="$l0"/>
                        </xsl:with-param>
                        <xsl:with-param name="l1">
                            <xsl:value-of select="$l1"/>
                        </xsl:with-param>
                        <xsl:with-param name="l2">
                            <xsl:value-of select="$l2"/>
                        </xsl:with-param>
                        <xsl:with-param name="l3">
                            <xsl:value-of select="$l3"/>
                        </xsl:with-param>
                        <xsl:with-param name="l4">
                            <xsl:value-of select="$l4"/>
                        </xsl:with-param>
                        <xsl:with-param name="l5">
                            <xsl:value-of select="$l5"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </resource>
            </xsl:if>

            <!-- Arbitrary Tags -->
            <xsl:for-each select="col[starts-with(@field, 'KV')]">
                <xsl:call-template name="KeyValue"/>
            </xsl:for-each>

            <!-- Impacts -->
            <xsl:for-each select="col[starts-with(@field, 'Impact')]">
                <xsl:call-template name="Impact">
                    <xsl:with-param name="Event">
                        <xsl:value-of select="$EventName"/>
                    </xsl:with-param>
                    <xsl:with-param name="l0">
                        <xsl:value-of select="$l0"/>
                    </xsl:with-param>
                    <xsl:with-param name="l1">
                        <xsl:value-of select="$l1"/>
                    </xsl:with-param>
                    <xsl:with-param name="l2">
                        <xsl:value-of select="$l2"/>
                    </xsl:with-param>
                    <xsl:with-param name="l3">
                        <xsl:value-of select="$l3"/>
                    </xsl:with-param>
                    <xsl:with-param name="l4">
                        <xsl:value-of select="$l4"/>
                    </xsl:with-param>
                    <xsl:with-param name="l5">
                        <xsl:value-of select="$l5"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="EventType">
        <xsl:param name="Type"/>
        <xsl:param name="SubType"/>
        <xsl:param name="SubSubType"/>

        <!-- @todo: migrate to Taxonomy-pattern, see vulnerability/data.xsl -->
        <resource name="event_event_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($EventTypePrefix, $Type)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Type"/></data>
        </resource>
        <xsl:if test="$SubType!=''">
            <resource name="event_event_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($EventTypePrefix, $Type, '/', $SubType)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$SubType"/></data>
                <reference field="parent" resource="event_event_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($EventTypePrefix, $Type)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>
        <xsl:if test="$SubSubType!=''">
            <resource name="event_event_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($EventTypePrefix, $Type, '/', $SubType, '/', $SubSubType)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$SubSubType"/></data>
                <reference field="parent" resource="event_event_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($EventTypePrefix, $Type, '/', $SubType)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Impact">
        <xsl:param name="Event"/>
        <xsl:param name="l0"/>
        <xsl:param name="l1"/>
        <xsl:param name="l2"/>
        <xsl:param name="l3"/>
        <xsl:param name="l4"/>
        <xsl:param name="l5"/>

        <xsl:variable name="ImpactType" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$Value!=''">
            <resource name="stats_impact">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('IMP:', $Event, '/', $l0, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5, '/', $ImpactType)"/>
                </xsl:attribute>
                <reference field="parameter_id" resource="stats_impact_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('IMPT:', $ImpactType)"/>
                    </xsl:attribute>
                </reference>
                <data field="value"><xsl:value-of select="$Value"/></data>
                <!-- Link to Location -->
                <xsl:call-template name="LocationReference">
                    <xsl:with-param name="l0">
                        <xsl:value-of select="$l0"/>
                    </xsl:with-param>
                    <xsl:with-param name="l1">
                        <xsl:value-of select="$l1"/>
                    </xsl:with-param>
                    <xsl:with-param name="l2">
                        <xsl:value-of select="$l2"/>
                    </xsl:with-param>
                    <xsl:with-param name="l3">
                        <xsl:value-of select="$l3"/>
                    </xsl:with-param>
                    <xsl:with-param name="l4">
                        <xsl:value-of select="$l4"/>
                    </xsl:with-param>
                    <xsl:with-param name="l5">
                        <xsl:value-of select="$l5"/>
                    </xsl:with-param>
                </xsl:call-template>
            </resource>
            <resource name="event_event_impact">
                <reference field="impact_id" resource="stats_impact">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('IMP:', $Event, '/', $l0, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5, '/', $ImpactType)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ImpactType">
        <xsl:variable name="ImpactType" select="normalize-space(substring-after(@field, ':'))"/>

        <resource name="stats_impact_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('IMPT:', $ImpactType)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$ImpactType"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="KeyValue">
        <xsl:variable name="Key" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$Value!=''">
            <resource name="event_event_tag">
                <data field="tag"><xsl:value-of select="$Key"/></data>
                <data field="value"><xsl:value-of select="$Value"/></data>
            </resource>
        </xsl:if>
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
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LocationReference">
        <xsl:param name="l0"/>
        <xsl:param name="l1"/>
        <xsl:param name="l2"/>
        <xsl:param name="l3"/>
        <xsl:param name="l4"/>
        <xsl:param name="l5"/>

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
        <xsl:variable name="l5id" select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>

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
