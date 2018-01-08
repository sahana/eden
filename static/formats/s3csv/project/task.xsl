<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Project Tasks - CSV Import Stylesheet

         CSV column...........Format..........Content

         Organisation.........string..........Project Organisation
         Project..............string..........Project Name
         Activity.............string..........Activity
         Activity Type........string..........Activity Type
         Incident.............string..........Incident
         Short Description ...string..........Task short description
         Detailed Description.string..........Task detailed description
         Date.................string..........Task created_on
         Author...............string..........Task created_by
         Source...............string..........Task source
         Assigned.............string..........Person Initials
         Date Due.............date............Task date_due
         Milestone............string..........Milestone name
         Time Estimated.......integer.........Task time_estimated 
         Priority.............string..........Task priority
         Status...............string..........Task status
         Country..............string..........Country code/name (L0)
         L1...................string..........L1 location name (e.g. State/Province)
         L2...................string..........L2 location name (e.g. District/County)
         L3...................string..........L3 location name (e.g. City)
         L4...................string..........L4 location name
         L5...................string..........L5 location name
         Lat..................float...........Latitude of the most local location
         Lon..................float...........Longitude of the most local location
         Comments.............string..........Task comments

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:variable name="ActivityTypePrefix" select="'ActivityType: '"/>

    <xsl:key name="organisations" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="projects" match="row" use="col[@field='Project']"/>
    <xsl:key name="activity types" match="row" use="col[@field='Activity Type']"/>
    <xsl:key name="activities" match="row" use="col[@field='Activity']"/>
    <xsl:key name="incidents" match="row" use="col[@field='Incident']"/>
    <xsl:key name="assignees" match="row" use="col[@field='Assigned']"/>
    <xsl:key name="milestones" match="row" use="col[@field='Milestone']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisations',
                                                                   col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Projects -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('projects',
                                                                   col[@field='Project'])[1])]">
                <xsl:call-template name="Project"/>
            </xsl:for-each>

            <!-- Activity Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('activity types',
                                                                   col[@field='Activity Type'])[1])]">
                <xsl:call-template name="ActivityType"/>
            </xsl:for-each>

            <!-- Activities -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('activities',
                                                                   col[@field='Activity'])[1])]">
                <xsl:call-template name="Activity"/>
            </xsl:for-each>

            <!-- Incidents -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('incidents',
                                                                   col[@field='Incident'])[1])]">
                <xsl:call-template name="Incident"/>
            </xsl:for-each>

            <!-- Assignees -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('assignees',
                                                                   col[@field='Assigned'])[1])]">
                <xsl:call-template name="Person"/>
            </xsl:for-each>
            
            <!-- Milestones -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('milestones',
                                                                   col[@field='Milestone'])[1])]">
                <xsl:call-template name="Milestone"/>
            </xsl:for-each>

            <!-- Tasks -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="ProjectName" select="col[@field='Project']/text()"/>
        <xsl:variable name="ActivityName" select="col[@field='Activity']/text()"/>
        <xsl:variable name="IncidentName" select="col[@field='Incident']/text()"/>
        <xsl:variable name="Task" select="col[@field='Short Description']/text()"/>
        <xsl:variable name="Date" select="col[@field='Date']/text()"/>
        <xsl:variable name="Author" select="col[@field='Author']/text()"/>
        <xsl:variable name="DateDue" select="col[@field='Date Due']/text()"/>
        <xsl:variable name="Milestone" select="col[@field='Milestone']/text()"/>
        <xsl:variable name="TimeEstimated" select="col[@field='Time Estimated']/text()"/>
        <xsl:variable name="Assignee" select="col[@field='Assigned']/text()"/>
        <xsl:variable name="Priority">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Priority']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Status" select="col[@field='Status']/text()"/>

        <resource name="project_task">
            <xsl:attribute name="created_on">
                <xsl:value-of select="$Date"/>
            </xsl:attribute>
            <xsl:attribute name="modified_on">
                <xsl:value-of select="$Date"/>
            </xsl:attribute>
            <xsl:attribute name="created_by">
                <xsl:value-of select="$Author"/>
            </xsl:attribute>
            <xsl:attribute name="modified_by">
                <xsl:value-of select="$Author"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Task"/></data>
            <data field="description"><xsl:value-of select="col[@field='Detailed Description']/text()"/></data>
            <data field="source"><xsl:value-of select="col[@field='Source']/text()"/></data>
            <xsl:choose>
                <xsl:when test="$Priority='URGENT'">
                    <data field="priority">1</data>
                </xsl:when>
                <xsl:when test="$Priority='HIGH'">
                    <data field="priority">2</data>
                </xsl:when>
                <xsl:when test="$Priority='MEDIUM'">
                    <data field="priority">3</data>
                </xsl:when>
                <xsl:when test="$Priority='NORMAL'">
                    <data field="priority">3</data>
                </xsl:when>
                <xsl:when test="$Priority='LOW'">
                    <data field="priority">4</data>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:choose>
                        <xsl:when test="$Priority!=''">
                            <!-- Assume an integer to just copy straight across -->
                            <data field="priority"><xsl:value-of select="$Priority"/></data>
                        </xsl:when>
                        <xsl:otherwise>
                            <!-- Assign a priority of 'Normal' -->
                            <data field="priority">3</data>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="$Status='Draft'">
                    <data field="status">1</data>
                </xsl:when>
                <xsl:when test="$Status='New'">
                    <data field="status">2</data>
                </xsl:when>
                <xsl:when test="$Status='Assigned'">
                    <data field="status">3</data>
                </xsl:when>
                <xsl:when test="$Status='Feedback'">
                    <data field="status">4</data>
                </xsl:when>
                <xsl:when test="$Status='Blocked'">
                    <data field="status">5</data>
                </xsl:when>
                <xsl:when test="$Status='On Hold'">
                    <data field="status">6</data>
                </xsl:when>
                <xsl:when test="$Status='Cancelled'">
                    <data field="status">7</data>
                </xsl:when>
                <xsl:when test="$Status='Duplicate'">
                    <data field="status">8</data>
                </xsl:when>
                <xsl:when test="$Status='Ready'">
                    <data field="status">9</data>
                </xsl:when>
                <xsl:when test="$Status='Verified'">
                    <data field="status">10</data>
                </xsl:when>
                <xsl:when test="$Status='Reopened'">
                    <data field="status">11</data>
                </xsl:when>
                <xsl:when test="$Status='Completed'">
                    <data field="status">12</data>
                </xsl:when>
                <xsl:when test="$Status='Closed'">
                    <!-- Completed -->
                    <data field="status">12</data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Open -->
                    <xsl:choose>
                        <xsl:when test="col[@field='Assigned']!=''">
                            <!-- Assigned -->
                            <data field="status">3</data>
                        </xsl:when>
                        <xsl:otherwise>
                            <!-- New -->
                            <data field="status">2</data>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>
            <!-- Date Due -->
            <data field="date_due">
                <xsl:value-of select="$DateDue"/>
                </data>
            <!-- Time Estimated -->
            <data field="time_estimated">
                <xsl:value-of select="$TimeEstimated"/>
            </data>
            <!-- Comment -->
            <xsl:if test="col[@field='Comments']/text()!=''">
                <resource name="project_comment">
                    <data field="body"><xsl:value-of select="col[@field='Comments']/text()"/></data>
                </resource>
            </xsl:if>

            <!-- Link to Assignee -->
            <xsl:if test="$Assignee!=''">
                <reference field="pe_id" resource="pr_person">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Assignee"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Link to Project -->
            <xsl:if test="$ProjectName!=''">
                <resource name="project_task_project">
                    <reference field="project_id" resource="project_project">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$ProjectName"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

            <!-- Link to Activity -->
            <xsl:if test="$ActivityName!=''">
                <resource name="project_task_activity">
                    <reference field="activity_id" resource="project_activity">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$ActivityName"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

            <!-- Link to Incident -->
            <xsl:if test="$IncidentName!=''">
                <resource name="event_task">
                    <reference field="incident_id" resource="event_incident">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$IncidentName"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

            <!-- Link to Location -->
            <xsl:call-template name="LocationReference"/>

            <!-- Link to Milestone -->
            <xsl:if test="$Milestone!=''">
                <resource name="project_task_milestone">
                    <reference field="milestone_id" resource="project_milestone">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$Milestone"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
        </resource>

        <!-- Locations -->
        <xsl:call-template name="Locations"/>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:variable name="OrganisationName" select="col[@field='Organisation']/text()"/>

        <xsl:if test="$OrganisationName!=''">
            <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OrganisationName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrganisationName"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Project">
        <xsl:variable name="ProjectName" select="col[@field='Project']/text()"/>
        <xsl:variable name="OrganisationName" select="col[@field='Organisation']/text()"/>

        <xsl:if test="$ProjectName!=''">
            <resource name="project_project">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ProjectName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$ProjectName"/></data>
                <!-- Link to Organisation -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrganisationName"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ActivityType">
        <xsl:call-template name="splitList">
            <xsl:with-param name="list">
                <xsl:value-of select="col[@field='Activity Type']"/>
            </xsl:with-param>
            <xsl:with-param name="arg">activity_type_res</xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>

        <xsl:choose>
            <xsl:when test="$arg='activity_type_ref'">
                <resource name="project_activity_activity_type">
                    <reference field="activity_type_id" resource="project_activity_type">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($ActivityTypePrefix, $item)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>
            <xsl:when test="$arg='activity_type_res'">
                <resource name="project_activity_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($ActivityTypePrefix, $item)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Activity">
        <xsl:variable name="ProjectName" select="col[@field='Project']/text()"/>
        <xsl:variable name="ActivityName" select="col[@field='Activity']/text()"/>
        <xsl:variable name="ActivityType" select="col[@field='Activity Type']/text()"/>

        <xsl:if test="$ActivityName!=''">
            <resource name="project_activity">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ActivityName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$ActivityName"/></data>

                <!-- Link to Project -->
                <reference field="project_id" resource="project_project">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$ProjectName"/>
                    </xsl:attribute>
                </reference>

                <!-- Link to Type -->
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list">
                        <xsl:value-of select="col[@field='Activity Type']"/>
                    </xsl:with-param>
                    <xsl:with-param name="arg">activity_type_ref</xsl:with-param>
                </xsl:call-template>

            </resource>
        </xsl:if>

        </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Incident">
        <xsl:variable name="IncidentName" select="col[@field='Incident']/text()"/>

        <resource name="event_incident">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$IncidentName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$IncidentName"/></data>
        </resource>

        </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">
        <xsl:variable name="Assignee" select="col[@field='Assigned']/text()"/>

        <xsl:if test="$Assignee!=''">
            <resource name="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Assignee"/>
                </xsl:attribute>
                <data field="initials"><xsl:value-of select="$Assignee"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Milestone">
        <xsl:variable name="ProjectName" select="col[@field='Project']/text()"/>
        <xsl:variable name="Milestone" select="col[@field='Milestone']/text()"/>

        <xsl:if test="$Milestone!=''">
            <resource name="project_milestone">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Milestone"/>
                </xsl:attribute>
                <!-- Link to Project -->
                <reference field="project_id" resource="project_project">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$ProjectName"/>
                    </xsl:attribute>
                </reference>
                <data field="name"><xsl:value-of select="$Milestone"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Locations">

        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="l5" select="col[@field='L5']/text()"/>

        <xsl:variable name="l1id" select="concat('L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('L4: ', $l4)"/>
        <xsl:variable name="l5id" select="concat('L5: ', $l5)"/>

        <xsl:variable name="lat" select="col[@field='Lat']"/>
        <xsl:variable name="lon" select="col[@field='Lon']"/>

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
                    <xsl:value-of select="$l1id"/>
                </xsl:attribute>
                <reference field="parent" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
                <data field="name"><xsl:value-of select="$l1"/></data>
                <data field="level"><xsl:text>L1</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="col[@field='L2'] or col[@field='L3'] or col[@field='L4']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="$lat"/></data>
                            <data field="lon"><xsl:value-of select="$lon"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
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
                <xsl:choose>
                    <xsl:when test="col[@field='L3'] or col[@field='L4']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="$lat"/></data>
                            <data field="lon"><xsl:value-of select="$lon"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
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
                <xsl:choose>
                    <xsl:when test="col[@field='L4']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="$lat"/></data>
                            <data field="lon"><xsl:value-of select="$lon"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
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
                <xsl:choose>
                    <xsl:when test="col[@field='L5']">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                            <data field="lat"><xsl:value-of select="$lat"/></data>
                            <data field="lon"><xsl:value-of select="$lon"/></data>
                        </xsl:if>
                     </xsl:otherwise>
                </xsl:choose>
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
                <xsl:if test="col[@field='Lat']!='' and col[@field='Lon']!=''">
                    <data field="lat"><xsl:value-of select="$lat"/></data>
                    <data field="lon"><xsl:value-of select="$lon"/></data>
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

        <xsl:variable name="l1id" select="concat('L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('L4: ', $l4)"/>
        <xsl:variable name="l5id" select="concat('L5: ', $l5)"/>

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
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
