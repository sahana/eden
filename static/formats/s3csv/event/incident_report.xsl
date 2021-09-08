<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Incident Report - CSV Import Stylesheet

         CSV fields:
         Event................................event_incident_report.event_id$name
         Incident.............................event_incident_report.incident_id$name
         Name.................................event_incident_report.name
         Type.................................event_incident_report.incident_type_id
         Date.................................event_incident_report.date
         Reported By..........................event_incident_report.reported_by
         Contact..............................event_incident_report.contact
         Country.................optional.....gis_location.L0 Name or ISO2
         L1......................optional.....gis_location.L1
         L2......................optional.....gis_location.L2
         L3......................optional.....gis_location.L3
         L4......................optional.....gis_location.L4
         L5......................optional.....gis_location.L5
         Building................optional.....gis_location.name
         Address.................optional.....gis_location.addr_street
         Postcode................optional.....gis_location.addr_postcode
         Lat..................................gis_location.lat
         Lon..................................gis_location.lon
         Description..........................event_incident_report.description
         Needs................................event_incident_report.needs
         Closed...............................event_incident_report.closed
         Organisation Group...................event_incident_report_group.group_id$name
         Comments.............................event_incident_report.comments

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

    <xsl:variable name="Postcode">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Postcode</xsl:with-param>
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
    <xsl:key name="events" match="row" use="col[@field='Event']"/>
    <xsl:key name="incidents" match="row" use="col[@field='Incident']"/>
    <xsl:key name="type" match="row" use="col[@field='Type']"/>
    <xsl:key name="organisation_group" match="row" use="col[@field='Organisation Group']"/>
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

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Type -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('type',
                                                                       col[@field='Type'])[1])]">
                <xsl:call-template name="Type"/>
            </xsl:for-each>

            <!-- Events -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('events',
                                                        col[@field='Event'])[1])]">
                <xsl:call-template name="Event"/>
            </xsl:for-each>

            <!-- Incidents -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('incidents',
                                                        col[@field='Incident'])[1])]">
                <xsl:call-template name="Incident"/>
            </xsl:for-each>

            <!-- Organisation Group -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation_group',
                                                                       col[@field='Organisation Group'])[1])]">
                <xsl:call-template name="OrganisationGroup"/>
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

            <!-- Incident Report -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Closed">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Closed']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="country">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Country"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="addr_street" select="col[@field='Address']/text()"/>
        <xsl:variable name="lat">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lat"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:if test="$Building!='' or $addr_street!='' or $lat!=''">
            <!-- Specific Location -->
            <xsl:call-template name="Location"/>
        </xsl:if>

        <!-- Incident Report -->
        <resource name="event_incident_report">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="date"><xsl:value-of select="col[@field='Date']"/></data>
            <data field="reported_by"><xsl:value-of select="col[@field='Reported By']"/></data>
            <data field="contact"><xsl:value-of select="col[@field='Contact']"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <data field="needs"><xsl:value-of select="col[@field='Needs']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            <xsl:choose>
                <xsl:when test="$Closed=''">
                    <!-- Use System Default -->
                </xsl:when>
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
            </xsl:choose>

            <xsl:if test="col[@field='Type']!=''">
                <reference field="incident_type_id" resource="event_incident_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Type:', col[@field='Type'])"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Person
            <xsl:if test="col[@field='Reported By First Name']">
                <reference field="person_id" resource="pr_person">
                    <resource name="pr_person">
                        <data field="first_name"><xsl:value-of select="col[@field='Reported By First Name']"/></data>
                        <data field="last_name"><xsl:value-of select="col[@field='Reported By Last Name']"/></data>
                        <xsl:if test="col[@field='Reported By Email']!=''">
                            <resource name="pr_contact">
                                <data field="contact_method" value="EMAIL"/>
                                <data field="value">
                                    <xsl:value-of select="col[@field='Reported By Email']/text()"/>
                                </data>
                            </resource>
                        </xsl:if>
                
                        <xsl:if test="col[@field='Reported By Phone']!=''">
                            <resource name="pr_contact">
                                <data field="contact_method" value="HOME_PHONE"/>
                                <data field="value">
                                    <xsl:value-of select="col[@field='Reported By Phone']/text()"/>
                                </data>
                            </resource>
                        </xsl:if>
                    </resource>
                </reference>
            </xsl:if> -->

            <!-- Link to Location -->
            <xsl:if test="$country!='' or $Building!='' or $addr_street!='' or $lat!=''">
                <xsl:call-template name="LocationReference"/>
            </xsl:if>

            <!-- Link to Event. Done via Incident
            <xsl:if test="col[@field='Event']!=''">
                <resource name="event_incident_report_event">
                    <reference field="event_id" resource="event_event">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Event:', col[@field='Event'])"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if> -->

            <!-- Link to Incident -->
            <xsl:if test="col[@field='Incident']!=''">
                <resource name="event_incident_report_incident">
                    <reference field="incident_id" resource="event_incident">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Incident:', col[@field='Incident'])"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

            <!-- Link to Organisation Group -->
            <xsl:if test="col[@field='Organisation Group']!=''">
                <resource name="event_incident_report_group">
                    <reference field="group_id" resource="org_group">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('OrganisationGroup:', col[@field='Organisation Group'])"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Type">

        <xsl:variable name="Type" select="col[@field='Type']"/>

        <xsl:if test="$Type!=''">
            <resource name="event_incident_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Type:', $Type)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Type"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Event">
        <xsl:variable name="Event" select="col[@field='Event']"/>

        <xsl:if test="$Event!=''">
            <resource name="event_event">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Event:', $Event)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Event"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Incident">
        <xsl:variable name="Incident" select="col[@field='Incident']"/>
        <xsl:variable name="Event" select="col[@field='Event']"/>
        <xsl:variable name="country">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Country"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="addr_street" select="col[@field='Address']/text()"/>
        <xsl:variable name="lat">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lat"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:if test="$Incident!=''">
            <resource name="event_incident">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Incident:', $Incident)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Incident"/></data>
                <xsl:if test="$Event!=''">
                    <reference field="event_id" resource="event_event">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Event:', $Event)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>

                <!-- Inherit Type & Location from Report -->
                <xsl:if test="col[@field='Type']!=''">
                    <reference field="incident_type_id" resource="event_incident_type">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Type:', col[@field='Type'])"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>

                <!-- Link to Location -->
                <xsl:if test="$country!='' or $Building!='' or $addr_street!='' or $lat!=''">
                    <xsl:call-template name="LocationReference"/>
                </xsl:if>

            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="OrganisationGroup">

        <xsl:variable name="OrganisationGroup" select="col[@field='Organisation Group']"/>

        <xsl:if test="$OrganisationGroup!=''">
            <resource name="org_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('OrganisationGroup:', $OrganisationGroup)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrganisationGroup"/></data>
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

        <xsl:variable name="addr_street" select="col[@field='Address']/text()"/>
        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="lat">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lat"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="$Building!='' or $addr_street!='' or $lat!=''">
                <!-- Specific Location -->
                <xsl:variable name="lon">
                    <xsl:call-template name="GetColumnValue">
                        <xsl:with-param name="colhdrs" select="$Lon"/>
                    </xsl:call-template>
                </xsl:variable>
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location:', $Building, '/', $addr_street, '/', $lat, '/', $lon, '/')"/>
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

        <xsl:variable name="Name" select="col[@field='Building']/text()"/>
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
        <xsl:variable name="addr_street" select="col[@field='Address']/text()"/>
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
            <xsl:if test="$Name!=''">
                <data field="name"><xsl:value-of select="$Name"/></data>
            </xsl:if>
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