<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Missions - CSV Import Stylesheet

         CSV fields:
         Organisation............deploy_mission.organisation_id
         Name....................deploy_mission.name
         Date....................deploy_mission.modified_on
         Event Type..............event_event.event_type_id
         Country.................gis_location.L0
         Comments................deploy_mission.comments

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
    <xsl:key name="type" match="row" use="col[@field='Event Type']"/>
    <xsl:key name="orgs" match="row" use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Event Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('type',
                                                                       col[@field='Event Type'])[1])]">
                <xsl:call-template name="EventType" />
            </xsl:for-each>

            <!-- Orgs -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('orgs',
                                                        col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Missions -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="EventType" select="col[@field='Event Type']"/>
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <!-- Mission -->
        <resource name="deploy_mission">
            <xsl:if test="col[@field='Date']!=''">
                <xsl:attribute name="modified_on">
                    <xsl:value-of select="col[@field='Date']"/>
                </xsl:attribute>
            </xsl:if>

            <xsl:if test="$OrgName!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>

            <!-- Link to Event Type -->
            <reference field="event_type_id" resource="event_event_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($EventTypePrefix, $EventType)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Location(s) -->
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
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="EventType">
        <xsl:variable name="EventType">
            <xsl:value-of select="col[@field='Event Type']"/>
        </xsl:variable>

        <xsl:if test="$EventType!=''">
            <resource name="event_event_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($EventTypePrefix, $EventType)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$EventType"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OrgName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
