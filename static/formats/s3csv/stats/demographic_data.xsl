<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Demographics Data - CSV Import Stylesheet

         Column headers defined in this stylesheet:

         Demographic....................required.....demographic.name
         Description....................optional.....demographic.description
         Value..........................required.....demographic_data.value
         OR
         Demo:XXXX......................required.....demographic.name (Demographic = XX in column name, value = cell in row. Multiple allowed)

         Year...........................optional.....demographic_data.date/end_date
         Start Date.....................optional.....demographic_data.date
         End Date.......................optional.....demographic_data.end_date
         Source.........................optional.....doc_document.name
         Source Organisation............optional.....doc_document.organisation_id
         Source URL.....................optional.....doc_document.url
         Country........................optional.....gis_location.L0
         L1.............................optional.....gis_location.L1
         L2.............................optional.....gis_location.L2
         L3.............................optional.....gis_location.L3
         L4.............................optional.....gis_location.L4
         L5.............................optional.....gis_location.L5
         Address........................optional.....gis_location.addr_street
         Postcode.......................optional.....gis_location.addr_postcode
         Building.......................optional.....gis_location.name
         Lat............................optional.....gis_location.lat
         Lon............................optional.....gis_location.lon
         Approved.......................optional.....demographic_data.approved_by
                                                     Set to 'false' to not approve records.
                                                     Note this only works for prepop or users with acl.APPROVE rights
         
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
                             concat('|', @field, '|'))], '/', col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'], '/',
                         col[@field='L4'])"/>

    <xsl:key name="L5" match="row"
             use="concat(col[contains(
                             document('../labels.xml')/labels/column[@name='Country']/match/text(),
                             concat('|', @field, '|'))], '/', col[@field='L1'], '/',
                         col[@field='L2'], '/',
                         col[@field='L3'], '/',
                         col[@field='L4'], '/',
                         col[@field='L5'])"/>

    <xsl:key name="demographic" match="row" use="col[@field='Demographic']"/>
    <xsl:key name="org" match="row" use="col[@field='Source Organisation']"/>
    <xsl:key name="source" match="row" use="col[@field='Source']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('org',
                                                        col[@field='Source Organisation'])[1])]">
                <xsl:call-template name="Organisation" />
            </xsl:for-each>

            <!-- Sources -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('source',
                                                        col[@field='Source'])[1])]">
                <xsl:call-template name="Source" />
            </xsl:for-each>

            <!-- Demographics (1/row) -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('demographic',
                                                        col[@field='Demographic'])[1])]">
                <xsl:call-template name="Demographic" />
            </xsl:for-each>

            <!-- Demographics (multi/row) -->
            <xsl:for-each select="//row[1]/col[starts-with(@field, 'Demo:')]">
                <xsl:call-template name="DemographicMulti"/>
            </xsl:for-each>

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

            <!-- Demographic Data -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Create the variables -->
        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="addr_street" select="col[@field='Address']/text()"/>
        <xsl:variable name="lat">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lat"/>
            </xsl:call-template>
        </xsl:variable>

        <!-- Need to read columns outside the loop as otherwise path is wrong -->
        <xsl:variable name="value" select="col[@field='Value']"/>
        <xsl:variable name="year" select="col[@field='Year']"/>
        <xsl:variable name="start_date">
            <xsl:choose>
                <xsl:when test="$year!=''">
                    <xsl:value-of select="concat($year,'-01-01')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="col[@field='Start Date']"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="end_date">
            <xsl:choose>
                <xsl:when test="$year!=''">
                    <xsl:value-of select="concat($year,'-12-31')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="col[@field='End Date']"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="source" select="col[@field='Source']"/>
        <xsl:variable name="approved">
            <xsl:choose>
                <xsl:when test="col[@field='Approved']='false'">
                    <xsl:text>false</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>true</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$Building!='' or $addr_street!='' or $lat!=''">
            <!-- Specific Location -->
            <xsl:call-template name="Location"/>
        </xsl:if>

        <!-- Demographic Data -->
        <xsl:choose>
            <xsl:when test="$value!=''">
                <!-- Single Demographic per row -->
                <xsl:variable name="demographic" select="col[@field='Demographic']/text()"/>

                <resource name="stats_demographic_data">
                    <xsl:attribute name="approved">
                        <xsl:value-of select="$approved"/>
                    </xsl:attribute>
                    <data field="date"><xsl:value-of select="$start_date"/></data>
                    <data field="end_date"><xsl:value-of select="$end_date"/></data>
                    <data field="value"><xsl:value-of select="$value"/></data>

                    <!-- Link to Demographic -->
                    <reference field="parameter_id" resource="stats_demographic">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('stats_demographic/',$demographic)"/>
                        </xsl:attribute>
                    </reference>

                    <!-- Link to Source -->
                    <xsl:if test="$source!=''">
                        <reference field="source_id" resource="doc_document">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('doc_document/', $source)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:if>

                    <!-- Link to Location -->
                    <xsl:call-template name="LocationReference"/>

                </resource>
            </xsl:when>
            <xsl:otherwise>
                <!-- Multiple Demographics per row -->
                <xsl:for-each select="col[starts-with(@field, 'Demo:')]">
                    <xsl:variable name="Value" select="text()"/>
                    <xsl:if test="$Value!=''">
                        <xsl:variable name="demographic" select="normalize-space(substring-after(@field, ':'))"/>
                        <xsl:variable name="location_uid">
                            <xsl:call-template name="LocationUid"/>
                        </xsl:variable>
                        <xsl:variable name="tuid_or_uuid">
                             <xsl:choose>
                                <xsl:when test="$Building!='' or $addr_street!='' or $lat!=''
                                                or col[@field='L1']!='' or col[@field='L2']!=''
                                                or col[@field='L3']!='' or col[@field='L4']!='' or col[@field='L5']!=''">
                                    <xsl:text>tuid</xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <!-- Country -->
                                    <xsl:text>uuid</xsl:text>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:variable>
                        <xsl:call-template name="DemographicData">
                            <xsl:with-param name="demographic">
                                <xsl:value-of select="$demographic"/>
                            </xsl:with-param>
                            <xsl:with-param name="value">
                                <xsl:value-of select="$Value"/>
                            </xsl:with-param>
                            <xsl:with-param name="start_date">
                                <xsl:value-of select="$start_date"/>
                            </xsl:with-param>
                            <xsl:with-param name="end_date">
                                <xsl:value-of select="$end_date"/>
                            </xsl:with-param>
                            <xsl:with-param name="source">
                                <xsl:value-of select="$source"/>
                            </xsl:with-param>
                            <xsl:with-param name="approved">
                                <xsl:value-of select="$approved"/>
                            </xsl:with-param>
                            <xsl:with-param name="tuid_or_uuid">
                                <xsl:value-of select="$tuid_or_uuid"/>
                            </xsl:with-param>
                            <xsl:with-param name="location_uid">
                                <xsl:value-of select="$location_uid"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="DemographicData">
        <xsl:param name="demographic"/>
        <xsl:param name="value"/>
        <xsl:param name="start_date"/>
        <xsl:param name="end_date"/>
        <xsl:param name="source"/>
        <xsl:param name="approved"/>
        <xsl:param name="tuid_or_uuid"/>
        <xsl:param name="location_uid"/>

        <resource name="stats_demographic_data">
            <xsl:attribute name="approved">
                <xsl:value-of select="$approved"/>
            </xsl:attribute>
            <data field="date"><xsl:value-of select="$start_date"/></data>
            <data field="end_date"><xsl:value-of select="$end_date"/></data>
            <data field="value"><xsl:value-of select="$value"/></data>

            <!-- Link to Demographic -->
            <reference field="parameter_id" resource="stats_demographic">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('stats_demographic/',$demographic)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Source -->
            <xsl:if test="$source!=''">
                <reference field="source_id" resource="doc_document">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('doc_document/', $source)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Link to Location -->
            <reference field="location_id" resource="gis_location">
                <xsl:choose>
                    <xsl:when test="$tuid_or_uuid='tuid'">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$location_uid"/>
                        </xsl:attribute>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- Country -->
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$location_uid"/>
                        </xsl:attribute>
                    </xsl:otherwise>
                </xsl:choose>
        </reference>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Demographic">
        <xsl:variable name="name" select="col[@field='Demographic']"/>
        <xsl:variable name="desc" select="col[@field='Description']"/>

        <resource name="stats_demographic">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('stats_demographic/',$name)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$name"/></data>
            <xsl:if test="$desc!=''">
                <data field="description"><xsl:value-of select="$desc"/></data>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="DemographicMulti">
        <xsl:variable name="name" select="normalize-space(substring-after(@field, ':'))"/>

        <resource name="stats_demographic">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('stats_demographic/',$name)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$name"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:variable name="OrgName" select="col[@field='Source Organisation']"/>

         <xsl:if test="$OrgName!=''">
             <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('organisation/',$OrgName)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrgName"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Source">
        <xsl:variable name="SourceName" select="col[@field='Source']"/>

        <xsl:if test="$SourceName!=''">
            <xsl:variable name="date" select="col[@field='Date']"/>
            <xsl:variable name="OrgName" select="col[@field='Source Organisation']"/>
            <xsl:variable name="url" select="col[@field='Source URL']"/>

            <resource name="doc_document">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('doc_document/',$SourceName)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$SourceName"/></data>
                <xsl:if test="$date!=''">
                    <data field="date"><xsl:value-of select="$date"/></data>
                </xsl:if>
                <xsl:if test="$OrgName!=''">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('organisation/',$OrgName)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
                <xsl:if test="$url!=''">
                    <data field="url"><xsl:value-of select="$url"/></data>
                </xsl:if>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LocationUid">
        <!-- Variant of LocationReference which just returns the tuid/uuid
             Needed when being used in a subsequent loop -->

        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="addr_street" select="col[@field='Address']/text()"/>
        <xsl:variable name="lat">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lat"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="$Building!='' or $addr_street!='' or $lat!=''">
                <!-- Specific Location -->
                <xsl:variable name="Name">
                    <xsl:choose>
                        <xsl:when test="$Building!=''">
                            <xsl:value-of select="$Building"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$addr_street"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="lon">
                    <xsl:call-template name="GetColumnValue">
                        <xsl:with-param name="colhdrs" select="$Lon"/>
                    </xsl:call-template>
                </xsl:variable>
                <!-- Return this -->
                <xsl:value-of select="concat('Location:', $Name, '/', $addr_street, '/', $lat, '/', $lon)"/>
            </xsl:when>

            <xsl:otherwise>
                <!-- Lx -->
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
                        <xsl:value-of select="$l5id"/>
                    </xsl:when>
                    <xsl:when test="$l4!=''">
                        <xsl:value-of select="$l4id"/>
                    </xsl:when>
                    <xsl:when test="$l3!=''">
                        <xsl:value-of select="$l3id"/>
                    </xsl:when>
                    <xsl:when test="$l2!=''">
                        <xsl:value-of select="$l2id"/>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <xsl:value-of select="$l1id"/>
                    </xsl:when>
                    <xsl:when test="$l0!=''">
                        <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>
                        <xsl:value-of select="$country"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:otherwise>
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

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

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

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

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

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

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

        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="addr_street" select="col[@field='Address']/text()"/>
        <xsl:variable name="lat">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lat"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="$Building!='' or $addr_street!='' or $lat!=''">
                <!-- Specific Location -->
                <xsl:variable name="Name">
                    <xsl:choose>
                        <xsl:when test="$Building!=''">
                            <xsl:value-of select="$Building"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$addr_street"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="lon">
                    <xsl:call-template name="GetColumnValue">
                        <xsl:with-param name="colhdrs" select="$Lon"/>
                    </xsl:call-template>
                </xsl:variable>
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location:', $Name, '/', $addr_street, '/', $lat, '/', $lon)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>

            <xsl:otherwise>
                <!-- Lx -->
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
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Location">

        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="addr_street" select="col[@field='Address']/text()"/>
        <xsl:variable name="Name">
            <xsl:choose>
                <xsl:when test="$Building!=''">
                    <xsl:value-of select="$Building"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$addr_street"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
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
        <xsl:variable name="addr_postcode">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Postcode"/>
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

        <xsl:variable name="l1id" select="concat('L1/', $countrycode, '/', $l1)"/>
        <xsl:variable name="l2id" select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
        <xsl:variable name="l3id" select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
        <xsl:variable name="l4id" select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
        <xsl:variable name="l5id" select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>

        <!-- Specific Location -->
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Location:', $Name, '/', $addr_street, '/', $lat, '/', $lon)"/>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="$l5!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l5id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
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
            <data field="name"><xsl:value-of select="$Name"/></data>
            <xsl:if test="$addr_street!=''">
                <data field="addr_street"><xsl:value-of select="$addr_street"/></data>
            </xsl:if>
            <xsl:if test="$addr_postcode!=''">
                <data field="addr_postcode"><xsl:value-of select="$addr_postcode"/></data>
            </xsl:if>
            <xsl:if test="$lat!=''">
                <data field="lat"><xsl:value-of select="$lat"/></data>
            </xsl:if>
            <xsl:if test="$lon!=''">
                <data field="lon"><xsl:value-of select="$lon"/></data>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
