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

         Date...........................optional.....demographic_data.date
         Source.........................optional.....stats_source.name
         Source URL.....................optional.....stats_source.url
         Country........................optional.....gis_location.L0
         L1.............................optional.....gis_location.L1
         L2.............................optional.....gis_location.L2
         L3.............................optional.....gis_location.L3
         L4.............................optional.....gis_location.L4
         L5.............................optional.....gis_location.L5
         Name...........................optional.....gis_location.name
         Approved.......................optional.....demographic_data.approved_by
                                                     Set to 'false' to not approve records.
                                                     Note this only works for prepop or users with acl.APPROVE rights
         
    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:key name="location"
             match="row"
             use="concat(col[@field='Country'],
                         col[@field='L1'],
                         col[@field='L2'],
                         col[@field='L3'],
                         col[@field='L4'])"/>

    <xsl:key name="group"
             match="row"
             use="concat(col[@field='Source'],
                         col[@field='Date'],
                         col[@field='Country'],
                         col[@field='L1'],
                         col[@field='L2'],
                         col[@field='L3'],
                         col[@field='L4'])"/>

    <xsl:key name="demographic"
             match="row"
             use="col[@field='Demographic']"/>

    <xsl:key name="source"
             match="row"
             use="col[@field='Source']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Create the Stats Group Type -->
            <resource name="stats_group_type">
                <xsl:attribute name="tuid">stats_group_type/stats_demographic</xsl:attribute>
                <data field="name">stats_demographic</data>
            </resource>

            <!-- Create the Demographics -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('demographic',
                                                        col[@field='Demographic'])[1])]">
                <xsl:call-template name="Demographic" />
            </xsl:for-each>

            <!-- Create the Sources -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('source',
                                                        col[@field='Source'])[1])]">
                <xsl:call-template name="Source" />
            </xsl:for-each>

            <!-- Create the Locations -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('location',
                                                        concat(col[@field='Country'],
                                                               col[@field='L1'],
                                                               col[@field='L2'],
                                                               col[@field='L3'],
                                                               col[@field='L4']))[1])]">
                <xsl:call-template name="Locations"/>
            </xsl:for-each>

            <!-- Create the Groups -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('group',
                                                        concat(col[@field='Source'],
                                                               col[@field='Date'],
                                                               col[@field='Country'],
                                                               col[@field='L1'],
                                                               col[@field='L2'],
                                                               col[@field='L3'],
                                                               col[@field='L4']))[1])]">
                <xsl:call-template name="Groups"/>
            </xsl:for-each>

            <!-- Create the Demographic Data records -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Demographic Data Record -->
    <xsl:template match="row">
        <xsl:choose>
            <xsl:when test="col[@field='Value']!=''">
                <!-- Single Demographic per row -->
                <xsl:call-template name="DemographicData">
                    <xsl:variable name="Demographic" select="col[@field='Demographic']"/>
                    <xsl:variable name="Value" select="col[@field='Value']"/>
                    <xsl:with-param name="demographic">
                        <xsl:value-of select="$Demographic"/>
                    </xsl:with-param>
                    <xsl:with-param name="value">
                        <xsl:value-of select="$Value"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <!-- Multiple Demographics per row -->
                <xsl:for-each select="col[starts-with(@field, 'Demo')]">
                    <xsl:variable name="Demographic" select="normalize-space(substring-after(@field, ':'))"/>
                    <xsl:variable name="Value" select="text()"/>
                    <xsl:if test="$Value!=''">
                        <xsl:call-template name="DemographicData">
                            <xsl:with-param name="demographic">
                                <xsl:value-of select="$Demographic"/>
                            </xsl:with-param>
                            <xsl:with-param name="value">
                                <xsl:value-of select="$Value"/>
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
        <xsl:variable name="date" select="col[@field='Date']"/>
        <xsl:variable name="location"><xsl:call-template name="LocationTuid"/></xsl:variable>
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

        <resource name="stats_demographic_data">
            <xsl:attribute name="approved">
                <xsl:value-of select="$approved"/>
            </xsl:attribute>
            <data field="date"><xsl:value-of select="$date"/></data>
            <data field="value"><xsl:value-of select="$value"/></data>

            <!-- Link to Demographic -->
            <reference field="parameter_id" resource="stats_demographic">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('stats_demographic/',$demographic)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Group -->
            <reference field="group_id" resource="stats_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('stats_group/',$location,'/',$date,'/',$source)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Location -->
            <xsl:call-template name="LocationReference"/>
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
    <xsl:template name="Groups">
        <xsl:variable name="status" select="col[@field='Status']"/>
        <xsl:variable name="date" select="col[@field='Date']"/>
        <xsl:variable name="location"><xsl:call-template name="LocationTuid"/></xsl:variable>
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

        <xsl:if test="col[@field='Value']!=''">
            <resource name="stats_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('stats_group/',$location,'/',$date,'/',$source)"/>
                </xsl:attribute>
                <xsl:attribute name="approved">
                    <xsl:value-of select="$approved"/>
                </xsl:attribute>
                <data field="date"><xsl:value-of select="$date"/></data>
                <data field="created_by">1</data>

                <!-- Link to Location -->
                <xsl:call-template name="LocationReference"/>

                <!-- Link to Source -->
                <reference field="source_id" resource="doc_document">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('doc_document/',$source)"/>
                    </xsl:attribute>
                </reference>

                <!-- Link to Group Type -->
                <reference field="group_type_id" resource="stats_group_type">
                    <xsl:attribute name="tuid">stats_group_type/stats_demographic</xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Source">
        <xsl:variable name="name" select="col[@field='Source']"/>

        <xsl:if test="$name!=''">
            <resource name="doc_document">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('doc_document/',$name)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$name"/></data>
                <data field="url"><xsl:value-of select="col[@field='Source URL']"/></data>
                <data field="date"><xsl:value-of select="col[@field='Date']"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LocationTuid">

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="l5" select="col[@field='L5']/text()"/>
        <xsl:variable name="Name" select="col[@field='Name']/text()"/>

        <xsl:choose>
            <xsl:when test="$Name!=''">
                <xsl:value-of select="concat('Location: ', $Name)"/>
            </xsl:when>
            <xsl:when test="$l5!=''">
                <xsl:value-of select="concat('Location L5: ', $l5)"/>
            </xsl:when>
            <xsl:when test="$l4!=''">
                <xsl:value-of select="concat('Location L4: ', $l4)"/>
            </xsl:when>
            <xsl:when test="$l3!=''">
                <xsl:value-of select="concat('Location L3: ', $l3)"/>
            </xsl:when>
            <xsl:when test="$l2!=''">
                <xsl:value-of select="concat('Location L2: ', $l2)"/>
            </xsl:when>
            <xsl:when test="$l1!=''">
                <xsl:value-of select="concat('Location L1: ', $l1)"/>
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
                            <xsl:value-of select="$l0"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>
                <xsl:value-of select="$country"/>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LocationReference">

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="l5" select="col[@field='L5']/text()"/>
        <xsl:variable name="Name" select="col[@field='Name']/text()"/>

        <reference field="location_id" resource="gis_location">
            <xsl:choose>
                <xsl:when test="$Name!=''">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location: ', $Name)"/>
                    </xsl:attribute>
                </xsl:when>
                <xsl:when test="$l5!=''">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location L5: ', $l5)"/>
                    </xsl:attribute>
                </xsl:when>
                <xsl:when test="$l4!=''">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location L4: ', $l4)"/>
                    </xsl:attribute>
                </xsl:when>
                <xsl:when test="$l3!=''">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location L3: ', $l3)"/>
                    </xsl:attribute>
                </xsl:when>
                <xsl:when test="$l2!=''">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location L2: ', $l2)"/>
                    </xsl:attribute>
                </xsl:when>
                <xsl:when test="$l1!=''">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location L1: ', $l1)"/>
                    </xsl:attribute>
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
                                <xsl:value-of select="$l0"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </xsl:when>
            </xsl:choose>
        </reference>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LocationPath">

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="l5" select="col[@field='L5']/text()"/>
        <xsl:variable name="Name" select="col[@field='Name']/text()"/>

        <xsl:if test="$Name!=''">
            <xsl:value-of select="$Name "/>
        </xsl:if>
        <xsl:if test="$l5!=''">
            <xsl:value-of select="$l5 "/>
        </xsl:if>
        <xsl:if test="$l4!=''">
            <xsl:value-of select="$l4 "/>
        </xsl:if>
        <xsl:if test="$l3!=''">
            <xsl:value-of select="$l3 "/>
        </xsl:if>
        <xsl:if test="$l2!=''">
            <xsl:value-of select="$l2 "/>
        </xsl:if>
        <xsl:if test="$l1!=''">
            <xsl:value-of select="$l1 "/>
        </xsl:if>
        <xsl:if test="$l0!=''">
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
            <xsl:value-of select="$country"/>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Locations">

        <xsl:variable name="Name" select="col[@field='Name']/text()"/>

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="l5" select="col[@field='L5']/text()"/>

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('Location L4: ', $l4)"/>
        <xsl:variable name="l5id" select="concat('Location L5: ', $l5)"/>
        <xsl:variable name="loc_id" select="concat('Location: ', $Name)"/>

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
            </resource>
        </xsl:if>

        <!-- Specific Location -->
        <xsl:if test="$Name!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$loc_id"/>
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
                <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
                <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

</xsl:stylesheet>
