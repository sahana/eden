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
         Address.................optional.....gis_location.addr_street
         Postcode................optional.....gis_location.addr_postcode
         Country.................optional.....gis_location.L0 Name or ISO2
         L1......................optional.....gis_location.L1
         L2......................optional.....gis_location.L2
         L3......................optional.....gis_location.L3
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

    <xsl:variable name="Postcode">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Postcode</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>


    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="events" match="row" use="col[@field='Event']"/>
    <xsl:key name="incidents" match="row" use="col[@field='Incident']"/>
    <xsl:key name="type" match="row" use="col[@field='Type']"/>
    <xsl:key name="organisation_group" match="row" use="col[@field='Organisation Group']"/>

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
            <reference field="location_id" resource="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Location:', col[@field='Address'], 
                                                              col[@field='Lat'], 
                                                              col[@field='Lon'],
                                                              col[@field='L3']
                                                              )"/>
                </xsl:attribute>
            </reference>

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
        
        <xsl:call-template name="Locations"/>

        <!-- Polygon -->
        <xsl:if test="col[@field='WKT']!=''">
            <resource name="gis_location">
                <xsl:call-template name="Location"/>
            </resource>
        </xsl:if>

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
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location:', col[@field='Address'], 
                                                                  col[@field='Lat'], 
                                                                  col[@field='Lon'],
                                                                  col[@field='L3']
                                                                  )"/>
                    </xsl:attribute>
                </reference>
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
    <xsl:template name="Locations">

        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>

        <xsl:variable name="postcode">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Postcode"/>
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
                    <xsl:value-of select="$l0"/>
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

        <!-- Location -->
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Location:', col[@field='Address'], 
                                                          col[@field='Lat'], 
                                                          col[@field='Lon'],
                                                          col[@field='L3'])"/>
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
            <data field="addr_street"><xsl:value-of select="col[@field='Address']"/></data>
            <data field="addr_postcode"><xsl:value-of select="$postcode"/></data>
            <xsl:if test="col[@field='Lat']!=''">
                <data field="lat"><xsl:value-of select="col[@field='Lat']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Lon']!=''">
                <data field="lon"><xsl:value-of select="col[@field='Lon']"/></data>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>