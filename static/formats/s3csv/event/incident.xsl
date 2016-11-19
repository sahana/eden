<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Incident - CSV Import Stylesheet

         CSV fields:
         Name.................................event_incident.name
         Type.................................event_incident.incident_type_id
         Event................................event_incident.event_id
         Exercise.............................event_incident.exercise
         Date.................................event_incident.date
         Closed...............................event_incident.closed
         Address.................optional.....gis_location.addr_street
         Postcode................optional.....gis_location.addr_postcode
         Country.................optional.....gis_location.L0 Name or ISO2
         L1......................optional.....gis_location.L1
         L2......................optional.....gis_location.L2
         L3......................optional.....gis_location.L3
         Lat..................................gis_location.lat
         Lon..................................gis_location.lon
         Lead Organisation....................event_incident.organisation_id
         Comments.............................event_incident.comments

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
    <xsl:key name="orgs" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="types" match="row" use="col[@field='Type']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('types',
                                                                       col[@field='Type'])[1])]">
                <xsl:call-template name="Type"/>
            </xsl:for-each>

            <!-- Events -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('events',
                                                        col[@field='Event'])[1])]">
                <xsl:call-template name="Event"/>
            </xsl:for-each>

            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('orgs',
                                                        col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Incident -->
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

        <!-- Incident -->
        <resource name="event_incident">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="date"><xsl:value-of select="col[@field='Date']"/></data>
            <xsl:choose>
                <xsl:when test="$Exercise=''">
                    <!-- Use System Default -->
                </xsl:when>
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
            </xsl:choose>
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

            <!-- Link to Type -->
            <xsl:if test="col[@field='Type']!=''">
                <reference field="incident_type_id" resource="event_incident_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Type:', col[@field='Type'])"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Link to Event -->
            <xsl:if test="col[@field='Event']!=''">
                <reference field="event_id" resource="event_event">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Event:', col[@field='Event'])"/>
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

            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Lead Organisaton']"/>
                </xsl:attribute>
            </reference>

            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
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
    <xsl:template name="Organisation">
        <xsl:variable name="OrgName" select="col[@field='Lead Organisation']/text()"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OrgName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
        </resource>

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