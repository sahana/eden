<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:project="http://eden.sahanafoundation.org/project">

    <!-- **********************************************************************
         Projects - CSV Import Stylesheet

         CSV column...........Format..........Content

         Organisation.........string..........Name of the Lead Organisation
         Event................string..........Event Name (optional)
         Project..............string..........Project Name
         Code.................string..........Project Code (optional)
         Description..........string..........Project short description
         Objectives...........string..........Project objectives
         Comments.............string..........Project comments
         Programme............string..........Project Programme
         Status...............string..........Project status
         Duration.............string..........Project duration
         Start Date...........YYYY-MM-DD......Start date of the project
         End Date.............YYYY-MM-DD......End date of the project
         Sectors..............;-sep list......List of Project Sectors (Allow Sector Names to include a Comma, such as "Water, Sanitation & Hygiene"
         Hazards..............comma-sep list..List of Hazard names
         HFA..................comma-sep list..List of HFA priorities (integer numbers)
         Budget...............double          Total Budget of project
         Budget:XXXX..........float...........Budget for year XXX (multiple allowed)
         FPFirstName..........string..........First Name of Focal Person
         FPLastName...........string..........Last Name of Focal Person
         FPEmail..............string..........Email Address of Focal Person
         FPMobilePhone........string..........Mobile Phone Number of Focal Person

         theme_percentages=True:
         Theme:XXXX...........string..........% of the Project targeting Theme XXX (multiple allowed)
         theme_percentages=False:
         Themes...............comma-sep list..List of Theme names

         Location:XXXX........string..........% of the Project targeting Location XXX (multiple allowed)
         theme_percentages=False:
         Locations............comma-sep list..List of Location names
         Partners.............comma-sep list..List of Partner names (role = 2)
         Donors...............comma-sep list..List of Donor names

    *********************************************************************** -->

    <xsl:import href="programme.xsl"/>

    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <xsl:variable name="EventPrefix" select="'Event:'"/>
    <xsl:variable name="HazardPrefix" select="'Hazard:'"/>
    <xsl:variable name="LocationPrefix" select="'Location:'"/>
    <xsl:variable name="SectorPrefix" select="'Sector:'"/>
    <xsl:variable name="ThemePrefix" select="'Theme:'"/>

    <!-- ****************************************************************** -->
    <xsl:key name="orgs" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="events" match="row" use="col[@field='Event']"/>
    <xsl:key name="statuses" match="row" use="col[@field='Status']"/>
    <xsl:key name="programmes" match="row" use="col[@field='Programme']"/>

    <xsl:key name="FP" match="row"
             use="concat(col[@field='Organisation'], '/',
                         col[@field='FPFirstName'], '/',
                         col[@field='FPLastName'], '/',
                         col[@field='FPEmail'], '/',
                         col[@field='FPMobilePhone'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('orgs',
                                                        col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Events -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('events',
                                                                   col[@field='Event'])[1])]">
                <xsl:call-template name="Event"/>
            </xsl:for-each>

            <!-- Focal Persons -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('FP',
                                                        concat(col[@field='Organisation'], '/',
                                                               col[@field='FPFirstName'], '/',
                                                               col[@field='FPLastName'], '/',
                                                               col[@field='FPEmail'], '/',
                                                               col[@field='FPMobilePhone']))[1])]">
                <xsl:call-template name="FocalPerson"/>
            </xsl:for-each>

            <!-- Statuses -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('statuses',
                                                        col[@field='Status'])[1])]">
                <xsl:call-template name="Status"/>
            </xsl:for-each>

            <!-- Programmes -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('programmes',
                                                        col[@field='Programme'])[1])]">
                <xsl:call-template name="Programme">
                    <xsl:with-param name="Field">Programme</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Themes -->
            <xsl:for-each select="//row[1]/col[starts-with(@field, 'Theme')]">
                <xsl:call-template name="Theme"/>
            </xsl:for-each>

            <!-- Locations -->
            <xsl:for-each select="//row[1]/col[starts-with(@field, 'Location')]">
                <xsl:call-template name="Location"/>
            </xsl:for-each>

            <!-- Projects -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="Event" select="col[@field='Event']/text()"/>

        <!-- Optional Classifications -->
        <xsl:variable name="Status" select="col[@field='Status']"/>
        <xsl:variable name="Hazards" select="col[@field='Hazards']"/>
        <xsl:variable name="HFA" select="col[@field='HFA']"/>
        <xsl:variable name="Sectors" select="col[@field='Sectors']"/>
        <xsl:variable name="Themes" select="col[@field='Themes']"/>
        <xsl:variable name="Locations" select="col[@field='Locations']"/>
        <xsl:variable name="Partners" select="col[@field='Partners']"/>
        <xsl:variable name="Donors" select="col[@field='Donors']"/>

        <xsl:variable name="FirstName" select="col[@field='FPFirstName']/text()"/>
        <xsl:variable name="LastName" select="col[@field='FPLastName']/text()"/>

        <!-- Projects -->
        <resource name="project_project">
            <data field="code"><xsl:value-of select="col[@field='Code']"/></data>
            <data field="name"><xsl:value-of select="col[@field='Project']"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <xsl:if test="col[@field='Start Date']!=''">
                <data field="start_date"><xsl:value-of select="col[@field='Start Date']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='End Date']!=''">
                <data field="end_date"><xsl:value-of select="col[@field='End Date']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Duration']!=''">
                <data field="duration"><xsl:value-of select="col[@field='Duration']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Objectives']!=''">
                <data field="objectives"><xsl:value-of select="col[@field='Objectives']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Budget']!=''">
                <data field="budget"><xsl:value-of select="col[@field='Budget']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>

            <!-- Programme -->
            <xsl:call-template name="ProgrammeLink"/>

            <!-- Status -->
            <xsl:if test="$Status">
                <reference field="status_id" resource="project_status">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Status"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Link to Event -->
            <xsl:if test="$Event!=''">
                <resource name="event_project">
                    <reference field="event_id" resource="event_event">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($EventPrefix, $Event)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

            <!-- HFAs -->
            <xsl:if test="$HFA!=''">
                <resource name="project_drr">
                    <data field="hfa">
                        <xsl:attribute name="value">
                            <xsl:value-of select="concat('[', $HFA, ']')"/>
                        </xsl:attribute>
                    </data>
                </resource>
            </xsl:if>

            <!-- Project Sectors -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list">
                    <xsl:value-of select="$Sectors"/>
                </xsl:with-param>
                <xsl:with-param name="listsep" select="';'"/>
                <xsl:with-param name="arg">sector_ref</xsl:with-param>
            </xsl:call-template>

            <!-- Project Hazards -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list">
                    <xsl:value-of select="$Hazards"/>
                </xsl:with-param>
                <xsl:with-param name="arg">hazard_ref</xsl:with-param>
            </xsl:call-template>

            <!-- Project Themes -->
            <!-- theme_percentages=False -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list">
                    <xsl:value-of select="$Themes"/>
                </xsl:with-param>
                <xsl:with-param name="arg">theme_ref</xsl:with-param>
            </xsl:call-template>
            <!-- theme_percentages=True -->
            <xsl:for-each select="col[starts-with(@field, 'Theme')]">
                <xsl:choose>
                    <xsl:when test="@field='Themes'">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:variable name="Theme" select="normalize-space(substring-after(@field, ':'))"/>
                        <xsl:variable name="Percentage" select="text()"/>
                        <xsl:if test="$Theme!='' and $Percentage!='' and $Percentage!='0'">
                            <resource name="project_theme_project">
                                <reference field="theme_id" resource="project_theme">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="concat($ThemePrefix, $Theme)"/>
                                    </xsl:attribute>
                                </reference>
                                <xsl:if test="$Percentage!=''">
                                    <data field="percentage"><xsl:value-of select="$Percentage"/></data>
                                </xsl:if>
                            </resource>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>

            <!-- Project Locations -->
            <!-- theme_percentages=False -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list">
                    <xsl:value-of select="$Locations"/>
                </xsl:with-param>
                <xsl:with-param name="arg">location_ref</xsl:with-param>
            </xsl:call-template>
            <xsl:for-each select="col[starts-with(@field, 'Location')]">
                <xsl:choose>
                    <xsl:when test="@field='Locations'">
                        <!-- theme_percentages=False -->
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- theme_percentages=True -->
                        <xsl:variable name="Location" select="normalize-space(substring-after(@field, ':'))"/>
                        <xsl:variable name="Percentage" select="text()"/>
                        <xsl:if test="$Percentage!='' and $Percentage!='0'">
                            <resource name="project_location">
                                <reference field="location_id" resource="gis_location">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="concat($LocationPrefix, $Location)"/>
                                    </xsl:attribute>
                                </reference>
                                <data field="percentage"><xsl:value-of select="$Percentage"/></data>
                            </resource>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>

            <!-- Partners -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list">
                    <xsl:value-of select="$Partners"/>
                </xsl:with-param>
                <xsl:with-param name="arg">partner_res</xsl:with-param>
            </xsl:call-template>

            <!-- Donors -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list">
                    <xsl:value-of select="$Donors"/>
                </xsl:with-param>
                <xsl:with-param name="arg">donor_res</xsl:with-param>
            </xsl:call-template>

            <!-- Project Organisations -->
            <!-- Embedded within record -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('ProjectOrganisation:', $OrgName)"/>
                </xsl:attribute>
            </reference>
            <!-- As link-table on Tab (comes onaccept) -->
            <!--<resource name="project_organisation">-->
                <!-- Lead Organisation (e.g. Host National Society) -->
                <!--<data field="role">1</data>
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('ProjectOrganisation:', $OrgName)"/>
                    </xsl:attribute>
                </reference>
            </resource>-->

            <!-- Project Budgets -->
            <xsl:variable name="Currency" select="col[@field='Currency']"/>
            <xsl:for-each select="col[starts-with(@field, 'Budget:')]">
                <xsl:variable name="Amount" select="text()"/>
                <xsl:if test="$Amount!=''">
                    <resource name="project_annual_budget">
                        <data field="year"><xsl:value-of select="normalize-space(substring-after(@field, ':'))"/></data>
                        <data field="amount"><xsl:value-of select="$Amount"/></data>
                        <data field="currency_type"><xsl:value-of select="$Currency"/></data>
                    </resource>
                </xsl:if>
            </xsl:for-each>

            <!-- Focal Point -->
            <xsl:if test="$FirstName!=''">
                <reference field="human_resource_id" resource="hrm_human_resource">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('HR:', $LastName, ',', $FirstName)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

        </resource>

        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$Sectors"/></xsl:with-param>
            <xsl:with-param name="listsep" select="';'"/>
            <xsl:with-param name="arg">sector_res</xsl:with-param>
        </xsl:call-template>

        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$Hazards"/></xsl:with-param>
            <xsl:with-param name="arg">hazard_res</xsl:with-param>
        </xsl:call-template>

        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$Themes"/></xsl:with-param>
            <xsl:with-param name="arg">theme_res</xsl:with-param>
        </xsl:call-template>

        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="$Locations"/></xsl:with-param>
            <xsl:with-param name="arg">location_res</xsl:with-param>
        </xsl:call-template>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>

        <xsl:choose>
            <!-- Sectors -->
            <xsl:when test="$arg='sector_ref'">
                <resource name="project_sector_project">
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
            <!-- Hazards -->
            <xsl:when test="$arg='hazard_ref'">
                <resource name="project_hazard_project">
                    <reference field="hazard_id" resource="project_hazard">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($HazardPrefix, $item)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>
            <xsl:when test="$arg='hazard_res'">
                <resource name="project_hazard">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($HazardPrefix, $item)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>
            <!-- Themes -->
            <xsl:when test="$arg='theme_ref'">
                <resource name="project_theme_project">
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
            <!-- Locations -->
            <xsl:when test="$arg='location_ref'">
                <resource name="project_location">
                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($LocationPrefix, $item)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>
            <xsl:when test="$arg='location_res'">
                <resource name="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($LocationPrefix, $item)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>
            <!-- Partners -->
            <xsl:when test="$arg='partner_res'">
                <resource name="project_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$item"/>
                    </xsl:attribute>
                    <reference field="organisation_id" resource="org_organisation">
                        <resource name="org_organisation">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$item"/>
                            </xsl:attribute>
                            <data field="name"><xsl:value-of select="$item"/></data>
                        </resource>
                    </reference>
                    <data field="role">2</data>
                </resource>
            </xsl:when>
            <!-- Donors -->
            <xsl:when test="$arg='donor_res'">
                <resource name="project_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$item"/>
                    </xsl:attribute>
                    <reference field="organisation_id" resource="org_organisation">
                        <resource name="org_organisation">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$item"/>
                            </xsl:attribute>
                            <data field="name"><xsl:value-of select="$item"/></data>
                        </resource>
                    </reference>
                    <data field="role">3</data>
                </resource>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('ProjectOrganisation:', $OrgName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
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
    <xsl:template name="Status">
        <xsl:variable name="Status" select="col[@field='Status']/text()"/>

        <resource name="project_status">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Status"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Status"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Theme">
        <xsl:variable name="Theme" select="normalize-space(substring-after(@field, ':'))"/>

        <xsl:if test="$Theme!=''">
            <resource name="project_theme">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($ThemePrefix, $Theme)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Theme"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Location">
        <xsl:variable name="Location" select="normalize-space(substring-after(@field, ':'))"/>

        <xsl:if test="$Location!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($LocationPrefix, $Location)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Location"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="FocalPerson">
        <xsl:variable name="FirstName" select="col[@field='FPFirstName']/text()"/>
        <xsl:variable name="LastName" select="col[@field='FPLastName']/text()"/>
        <xsl:variable name="Email" select="col[@field='FPEmail']/text()"/>
        <xsl:variable name="MobilePhone" select="col[@field='FPMobilePhone']/text()"/>
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="pr_person">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Person:', $LastName, ',', $FirstName)"/>
            </xsl:attribute>
            <data field="first_name"><xsl:value-of select="$FirstName"/></data>
            <data field="last_name"><xsl:value-of select="$LastName"/></data>
            <xsl:if test="$Email!=''">
                <resource name="pr_contact">
                    <data field="contact_method" value="EMAIL"/>
                    <data field="value"><xsl:value-of select="$Email"/></data>
                </resource>
            </xsl:if>
            <xsl:if test="$MobilePhone!=''">
                <resource name="pr_contact">
                    <data field="contact_method" value="SMS"/>
                    <data field="value"><xsl:value-of select="$MobilePhone"/></data>
                </resource>
            </xsl:if>
        </resource>

        <resource name="hrm_human_resource">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('HR:', $LastName, ',', $FirstName)"/>
            </xsl:attribute>
            <data field="type">1</data> <!-- Staff -->
            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">

                    <xsl:value-of select="concat('ProjectOrganisation:', $OrgName)"/>
                </xsl:attribute>
            </reference>
            <reference field="person_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Person:', $LastName, ',', $FirstName)"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
