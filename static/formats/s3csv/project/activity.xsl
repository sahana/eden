<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Project Activities - CSV Import Stylesheet

         CSV column...........Format..........Content

         Project..............string..........Project Name (optional)
         Event................string..........Event Name (optional)
         Activity.............string..........Activity short description
         Activity Type........;-sep list......List of Activity Types
         Sectors..............;-sep list......List of Activity Sectors (Allow Sector Names to include a Comma, such as "Water, Sanitation & Hygiene"
         Themes...............;-sep list......List of Activity Themes
         Organisation.........comma-sep list..project_activity_organisation.organisation_id role=1 (default)
         Partner..............comma-sep list..project_activity_organisation.organisation_id role=2
         Donor................comma-sep list..project_activity_organisation.organisation_id role=3
         Organisation Group...string..........project_activity_group.group_id
         Country..............string..........Country code/name (L0)
         L1...................string..........L1 location name (e.g. State/Province)
         L2...................string..........L2 location name (e.g. District/County)
         L3...................string..........L3 location name (e.g. City)
         L4...................string..........L4 location name (e.g. Neighborhood)
         L5...................string..........L5 location name
         Location.............string..........Specific location name (e.g. School)
         Lat..................float...........Latitude of the most local location
         Lon..................float...........Longitude of the most local location
         ContactPersonXXX.....comma-sep list..Contact Person (can be multiple columns)
                                              as "FirstName,LastName,Email,MobilePhone",
                                              where first name and email as well as the
                                              three commas are mandatory
         Start Date...........date............Start Date
         End Date.............date............End Date
         Comments.............string..........Activity Comments
         Item:XXX.............integer.........Number of Items of type XXX Distributed (multiple allowed)
         Beneficiaries:XXX...........integer..Number of Beneficiaries of type XXX (multiple allowed)
         TargetedBeneficiaries:XXX...integer..Targeted Number of Beneficiaries of type XXX

         Alternatively, Beneficiaries:XXX can be like "<actual_number>/<targeted_number>"

         @ToDo: Support lowest-level Lx as ;-separated list
                Do this by making the normal Activity Row part of a splitList

    *********************************************************************** -->

    <xsl:import href="beneficiary.xsl"/>

    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:variable name="ActivityTypePrefix" select="'ActivityType:'"/>
    <xsl:variable name="EventPrefix" select="'Event:'"/>
    <xsl:variable name="OrgPrefix" select="'Org:'"/>
    <xsl:variable name="ProjectPrefix" select="'Project:'"/>
    <xsl:variable name="SectorPrefix" select="'Sector:'"/>
    <xsl:variable name="StatusPrefix" select="'Status:'"/>
    <xsl:variable name="ThemePrefix" select="'Theme:'"/>

    <xsl:key name="events" match="row" use="col[@field='Event']"/>
    <xsl:key name="org_groups" match="row" use="col[@field='Organisation Group']"/>
    <xsl:key name="projects" match="row" use="col[@field='Project']"/>
    <xsl:key name="statuses" match="row" use="col[@field='Status']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Beneficiary Types -->
            <xsl:for-each select="//row[1]/col[starts-with(@field, 'Beneficiaries')]">
                <xsl:call-template name="BeneficiaryType"/>
            </xsl:for-each>

            <!-- Distribution Items -->
            <xsl:for-each select="//row[1]/col[starts-with(@field, 'Item')]">
                <xsl:call-template name="DistributionItem"/>
            </xsl:for-each>

            <!-- Events -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('events',
                                                                   col[@field='Event'])[1])]">
                <xsl:call-template name="Event"/>
            </xsl:for-each>

            <!-- Organisation Groups -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('org_groups',
                                                                       col[@field='Organisation Group'])[1])]">
                <xsl:call-template name="OrganisationGroup"/>
            </xsl:for-each>

            <!-- Projects -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('projects',
                                                                   col[@field='Project'])[1])]">
                <xsl:call-template name="Project"/>
            </xsl:for-each>

            <!-- Statuses -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('statuses',
                                                                   col[@field='Status'])[1])]">
                <xsl:call-template name="Status"/>
            </xsl:for-each>

            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Project" select="col[@field='Project']/text()"/>
        <xsl:variable name="Event" select="col[@field='Event']/text()"/>
        <xsl:variable name="Activity" select="col[@field='Activity']/text()"/>
        <xsl:variable name="ActivityType" select="col[@field='Activity Type']/text()"/>
        <xsl:variable name="Org" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="Partner" select="col[@field='Partner']/text()"/>
        <xsl:variable name="Donor" select="col[@field='Donor']/text()"/>
        <xsl:variable name="Sectors" select="col[@field='Sectors']/text()"/>
        <xsl:variable name="Status" select="col[@field='Status']/text()"/>
        <xsl:variable name="Themes" select="col[@field='Themes']/text()"/>

        <xsl:if test="$Activity !='' or col[starts-with(@field, 'Item')]/text() !=''">
            <resource name="project_activity">
                <data field="name"><xsl:value-of select="$Activity"/></data>
                <data field="date"><xsl:value-of select="col[@field='Start Date']"/></data>
                <data field="end_date"><xsl:value-of select="col[@field='End Date']"/></data>
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

                <!-- Link to Activity Types -->
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list">
                        <xsl:value-of select="$ActivityType"/>
                    </xsl:with-param>
                    <xsl:with-param name="listsep" select="';'"/>
                    <xsl:with-param name="arg">activity_type_ref</xsl:with-param>
                </xsl:call-template>

                <!-- Link to Beneficiaries -->
                <xsl:for-each select="col[starts-with(@field, 'Beneficiaries')]">
                    <xsl:call-template name="ActivityBeneficiaries">
                        <xsl:with-param name="ProjectName">
                            <xsl:value-of select="$Project"/>
                        </xsl:with-param>
                        <xsl:with-param name="ActivityName">
                            <xsl:value-of select="$Activity"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:for-each>

                <!-- Link to Contact -->
                <xsl:call-template name="ContactPersonReference"/>

                <!-- Link to Distributions -->
                <xsl:for-each select="col[starts-with(@field, 'Item')]">
                    <xsl:call-template name="Distribution" />
                </xsl:for-each>

                <!-- Link to Location -->
                <xsl:call-template name="LocationReference"/>

                <!-- Link to Organisations -->
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list">
                        <xsl:value-of select="$Org"/>
                    </xsl:with-param>
                    <xsl:with-param name="arg">org_ref</xsl:with-param>
                </xsl:call-template>

                <!-- Link to Partners -->
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list">
                        <xsl:value-of select="$Partner"/>
                    </xsl:with-param>
                    <xsl:with-param name="arg">org_ref</xsl:with-param>
                </xsl:call-template>

                <!-- Link to Donors -->
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list">
                        <xsl:value-of select="$Donor"/>
                    </xsl:with-param>
                    <xsl:with-param name="arg">org_ref</xsl:with-param>
                </xsl:call-template>

                <!-- Link to Organisation Group -->
                <xsl:if test="col[@field='Organisation Group']!=''">
                    <resource name="project_activity_group">
                        <reference field="group_id" resource="org_group">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('OrganisationGroup:',
                                                             col[@field='Organisation Group'])"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>

                <!-- Link to Project -->
                <xsl:if test="$Project!=''">
                    <reference field="project_id" resource="project_project">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($ProjectPrefix, $Project)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>

                <!-- Link to Event -->
                <xsl:if test="$Event!=''">
                    <resource name="event_activity">
                        <reference field="event_id" resource="event_event">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($EventPrefix, $Event)"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>

                <!-- Link to Sectors -->
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list">
                        <xsl:value-of select="$Sectors"/>
                    </xsl:with-param>
                    <xsl:with-param name="listsep" select="';'"/>
                    <xsl:with-param name="arg">sector_ref</xsl:with-param>
                </xsl:call-template>

                <!-- Link to Status -->
                <xsl:if test="$Status!=''">
                    <reference field="status_id" resource="project_status">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($StatusPrefix, $Status)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>

                <!-- Link to Themes -->
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list">
                        <xsl:value-of select="$Themes"/>
                    </xsl:with-param>
                    <xsl:with-param name="listsep" select="';'"/>
                    <xsl:with-param name="arg">theme_ref</xsl:with-param>
                </xsl:call-template>

            </resource>
        </xsl:if>

        <!-- Activity Types -->
        <xsl:call-template name="splitList">
            <xsl:with-param name="list">
                <xsl:value-of select="$ActivityType"/>
            </xsl:with-param>
            <xsl:with-param name="listsep" select="';'"/>
            <xsl:with-param name="arg">activity_type_res</xsl:with-param>
        </xsl:call-template>

        <!-- Beneficiaries -->
        <xsl:for-each select="col[starts-with(@field, 'Beneficiaries')]">
            <xsl:call-template name="Beneficiaries">
                <xsl:with-param name="ProjectName">
                    <xsl:value-of select="$Project"/>
                </xsl:with-param>
                <xsl:with-param name="ActivityName">
                    <xsl:value-of select="$Activity"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:for-each>

        <!-- Contacts -->
        <xsl:call-template name="ContactPerson"/>

        <!-- Locations -->
        <xsl:call-template name="Locations"/>

        <!-- Organisations -->
        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$Org"/></xsl:with-param>
            <xsl:with-param name="arg">org_res</xsl:with-param>
        </xsl:call-template>

        <!-- Partners -->
        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$Partner"/></xsl:with-param>
            <xsl:with-param name="arg">org_res</xsl:with-param>
            <xsl:with-param name="org">2</xsl:with-param>
        </xsl:call-template>

        <!-- Donors -->
        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$Donor"/></xsl:with-param>
            <xsl:with-param name="arg">org_res</xsl:with-param>
            <xsl:with-param name="org">3</xsl:with-param>
        </xsl:call-template>

        <!-- Sectors -->
        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$Sectors"/></xsl:with-param>
            <xsl:with-param name="listsep" select="';'"/>
            <xsl:with-param name="arg">sector_res</xsl:with-param>
        </xsl:call-template>

        <!-- Themes -->
        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$Themes"/></xsl:with-param>
            <xsl:with-param name="listsep" select="';'"/>
            <xsl:with-param name="arg">theme_res</xsl:with-param>
        </xsl:call-template>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>
        <xsl:param name="org"/>

        <xsl:choose>
            <!-- Activity Types -->
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
            <!-- Organisations -->
            <xsl:when test="$arg='org_ref'">
                <resource name="project_activity_organisation">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($OrgPrefix, $item)"/>
                        </xsl:attribute>
                    </reference>
                    <xsl:if test="$org!=''">
                        <data field="role"><xsl:value-of select="$org"/></data>
                    </xsl:if>
                </resource>
            </xsl:when>
            <xsl:when test="$arg='org_res'">
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($OrgPrefix, $item)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>
            <!-- Sectors -->
            <xsl:when test="$arg='sector_ref'">
                <resource name="project_sector_activity">
                    <reference field="sector_id" resource="org_sector">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($SectorPrefix, $item)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>
            <xsl:when test="$arg='sector_res'">
                <resource name="org_sector">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($SectorPrefix, $item)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>
            <!-- Themes -->
            <xsl:when test="$arg='theme_ref'">
                <resource name="project_theme_activity">
                    <reference field="theme_id" resource="project_theme">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($ThemePrefix, $item)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>
            <xsl:when test="$arg='theme_res'">
                <resource name="project_theme">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($ThemePrefix, $item)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ActivityType">

        <xsl:variable name="ActivityType" select="col[@field='Activity Type']"/>

        <xsl:if test="$ActivityType!=''">
            <resource name="project_activity_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('ActivityType:', $ActivityType)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$ActivityType"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ActivityBeneficiaries">
        <xsl:param name="ProjectName"/>
        <xsl:param name="ActivityName"/>

        <xsl:variable name="BeneficiaryType" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="BeneficiaryNumber" select="text()"/>

        <xsl:if test="$BeneficiaryNumber!=''">
            <resource name="project_beneficiary_activity">
                <reference field="beneficiary_id" resource="project_beneficiary">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('BNFNumber:',
                                                     $ProjectName, '/',
                                                     $ActivityName, '/',
                                                     $BeneficiaryType)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ContactPerson">

        <xsl:for-each select="col[starts-with(@field, 'ContactPerson')]">
            <xsl:variable name="PersonData" select="text()"/>
            <xsl:variable name="FirstName" select="substring-before($PersonData, ',')"/>
            <xsl:variable name="LastName" select="substring-before(substring-after($PersonData, ','), ',')"/>
            <xsl:variable name="Email" select="substring-before(substring-after(substring-after($PersonData, ','), ','), ',')"/>
            <xsl:variable name="MobilePhone" select="substring-after(substring-after(substring-after($PersonData, ','), ','), ',')"/>

            <xsl:if test="$FirstName!='' and $Email!=''">
                <resource name="pr_person">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Contact:', $Email)"/>
                    </xsl:attribute>
                    <data field="first_name"><xsl:value-of select="$FirstName"/></data>
                    <data field="last_name"><xsl:value-of select="$LastName"/></data>

                    <!-- Contacts -->
                    <resource name="pr_contact">
                        <data field="contact_method">EMAIL</data>
                        <data field="value"><xsl:value-of select="$Email"/></data>
                    </resource>
                    <xsl:if test="$MobilePhone!=''">
                        <resource name="pr_contact">
                            <data field="contact_method">SMS</data>
                            <data field="value"><xsl:value-of select="$MobilePhone"/></data>
                        </resource>
                    </xsl:if>
                </resource>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ContactPersonReference">

        <xsl:for-each select="col[starts-with(@field, 'ContactPerson')]">
            <xsl:variable name="PersonData" select="text()"/>
            <xsl:variable name="FirstName" select="substring-before($PersonData, ',')"/>
            <xsl:variable name="LastName" select="substring-before(substring-after($PersonData, ','), ',')"/>
            <xsl:variable name="Email" select="substring-before(substring-after(substring-after($PersonData, ','), ','), ',')"/>
            <xsl:variable name="MobilePhone" select="substring-after(substring-after(substring-after($PersonData, ','), ','), ',')"/>
            <xsl:if test="$FirstName!='' and $Email!=''">

                <resource name="project_activity_contact">
                    <reference field="person_id" resource="pr_person">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Contact:', $Email)"/>
                        </xsl:attribute>
                    </reference>
                </resource>

            </xsl:if>
        </xsl:for-each>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Distribution">
        <xsl:variable name="DistributionItem" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="ItemNumber" select="text()"/>

        <xsl:if test="$ItemNumber!=''">
            <resource name="supply_distribution">
                <reference field="parameter_id" resource="supply_distribution_item">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('DITEM:', $DistributionItem)"/>
                    </xsl:attribute>
                </reference>
                <data field="value"><xsl:value-of select="$ItemNumber"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="DistributionItem">
        <xsl:variable name="DistributionItem" select="normalize-space(substring-after(@field, ':'))"/>

        <resource name="supply_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('ITEM:', $DistributionItem)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$DistributionItem"/></data>
        </resource>

        <resource name="supply_distribution_item">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('DITEM:', $DistributionItem)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$DistributionItem"/></data>
            <reference field="item_id" resource="supply_item">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('ITEM:', $DistributionItem)"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Event">
        <xsl:variable name="Event" select="col[@field='Event']/text()"/>

        <xsl:if test="$Event!=''">
            <resource name="event_event">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($EventPrefix, $Event)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Event"/></data>
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
        <xsl:variable name="location" select="col[@field='Location']/text()"/>

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('Location L4: ', $l4)"/>
        <xsl:variable name="l5id" select="concat('Location L5: ', $l5)"/>
        <xsl:variable name="location_id" select="concat('Location: ', $location)"/>

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
                    <xsl:value-of select="$l0"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="country"
                      select="concat('urn:iso:std:iso:3166:-1:code:',
                                     $countrycode)"/>

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
                <xsl:choose>
                    <xsl:when test="$l4!=''">
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- We're the lowest level, so apply Lat/Lon here -->
                        <xsl:if test="$lat!='' and $lon!=''">
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
                    <xsl:when test="$l5!=''">
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- We're the lowest level, so apply Lat/Lon here -->
                        <xsl:if test="$lat!='' and $lon!=''">
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
                <xsl:choose>
                    <xsl:when test="$location!=''">
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- We're the lowest level, so apply Lat/Lon here -->
                        <xsl:if test="$lat!='' and $lon!=''">
                            <data field="lat"><xsl:value-of select="$lat"/></data>
                            <data field="lon"><xsl:value-of select="$lon"/></data>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>
        </xsl:if>

        <!-- Specific Location -->
        <xsl:if test="$location!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$location_id"/>
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
                <data field="name"><xsl:value-of select="$location"/></data>
                <xsl:if test="$lat!='' and $lon!=''">
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
        <xsl:variable name="location" select="col[@field='Location']/text()"/>

        <xsl:choose>
            <xsl:when test="$location!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location: ', $location)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l5!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Location L5: ', $l4)"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
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
                <xsl:variable name="country"
                              select="concat('urn:iso:std:iso:3166:-1:code:',
                                             $countrycode)"/>
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
        </xsl:choose>

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
    <xsl:template name="Project">
        <xsl:variable name="ProjectName" select="col[@field='Project']/text()"/>
        <xsl:variable name="listsep" select="','"/>
        <xsl:variable name="Organisations" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="OrgName">
            <xsl:choose>
                <xsl:when test="contains($Organisations, $listsep)">
                    <xsl:value-of select="substring-before($Organisations, $listsep)"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$Organisations"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$ProjectName!=''">
            <resource name="project_project">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($ProjectPrefix, $ProjectName)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$ProjectName"/></data>
                <!-- Org is a required field, so either need to import Projects 1st or set Org here -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($OrgPrefix, $OrgName)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Status">
        <xsl:variable name="StatusName" select="col[@field='Status']/text()"/>

        <xsl:if test="$StatusName!=''">
            <resource name="project_status">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($StatusPrefix, $StatusName)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$StatusName"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>