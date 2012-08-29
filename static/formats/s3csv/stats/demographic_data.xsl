<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Demographics Data - CSV Import Stylesheet

         Column headers defined in this stylesheet:

         Demographic....................required.....demographic.name
         Description....................optional.....demographic.description
         Value..........................required.....demographic_data.value
         Date...........................optional.....demographic_data.name
         Source Name....................optional.....stats_source.name
         Source URL.....................optional.....stats_source.url
         Country........................optional.....gis_location.L0
         L1.............................optional.....gis_location.L1
         L2.............................optional.....gis_location.L2
         L3.............................optional.....gis_location.L3
         L4.............................optional.....gis_location.L4
         Name...........................optional.....gis_location.name

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

    <xsl:key name="demographic"
             match="row"
             use="col[@field='Demographic']"/>

    <xsl:key name="source"
             match="row"
             use="col[@field='Source Name']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Create the Doc Source Type -->
            <resource name="doc_source_type">
                <xsl:attribute name="tuid">doc_source_type_stats_demographic</xsl:attribute>
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
                                                        col[@field='Source Name'])[1])]">
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

            <!-- Create the Demographic Data records -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Demographic Data Record -->
    <xsl:template match="row">

        <resource name="stats_demographic_data">
            <data field="value"><xsl:value-of select="col[@field='Value']"/></data>
            <data field="date"><xsl:value-of select="col[@field='Date']"/></data>

            <!-- Link to Demographic -->
            <reference field="parameter_id" resource="stats_demographic">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('stats_demographic/',col[@field='Demographic'])"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Source -->
            <reference field="source_id" resource="stats_source">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('stats_source/',col[@field='Source Name'])"/>
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
    <xsl:template name="Source">
        <xsl:variable name="name" select="col[@field='Source Name']"/>

        <xsl:if test="$name!=''">
            <resource name="stats_source">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('stats_source/',$name)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$name"/></data>
                <data field="url"><xsl:value-of select="col[@field='Source URL']"/></data>
                <data field="date"><xsl:value-of select="col[@field='Date']"/></data>
                <data field="status">Approval pending</data>
                <data field="created_by">1</data>
                <!-- Link to Location -->
                <xsl:call-template name="LocationReference"/>

                <!-- Link to Source Type -->
                <reference field="source_type_id" resource="doc_source_type">
                    <xsl:attribute name="tuid">doc_source_type_stats_demographic</xsl:attribute>
                </reference>
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

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('Location L4: ', $l4)"/>

        <xsl:choose>
            <xsl:when test="$l4!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location L4: ', $l4)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l3!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location L3: ', $l3)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l2!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location L2: ', $l2)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l1!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location L1: ', $l1)"/>
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
                            <xsl:value-of select="$l0"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Locations">

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('Location L4: ', $l4)"/>

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

    </xsl:template>

</xsl:stylesheet>
