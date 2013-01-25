<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Project Locations - CSV Import Stylesheet

         CSV column...........Format..........Content

         Project Code.........string..........Project Code (need code or name)
         Project Name.........string..........Project Name
         Project Comments.....string..........Project comments
         Status...............string..........Project status
         Donor Organisations..
         Start Date...........YYYY-MM-DD......Start date of the project
         End Date.............YYYY-MM-DD......End date of the project
         Activity Types.......comma-sep list..List of Activity Types
         Country..............string..........Country code/name (L0)
         L1...................string..........L1 location name (State/Province)
         L2...................string..........L1 location name (District)
         L3...................string..........L3 location name (City)
         L4...................string..........L4 location name
         L5...................string..........L5 location name
         Lat..................float...........Latitude of the most local location
         Lon..................float...........Longitude of the most local location
         Comments.............string..........Comments
         ContactPersonXX......comma-sep list..Contact Person (can be multiple columns)
                                              as "FirstName,LastName,Email,MobilePhone",
                                              where first name and email as well as the
                                              three commas are mandatory
         Beneficiaries:XXX....integer.........Number of Beneficiaries of type XXX (multiple allowed)

    *********************************************************************** -->

    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:variable name="ActivityTypePrefix" select="'ActivityType: '"/>

    <xsl:key name="orgs"
             match="row"
             use="col[@field='Lead Organisation']"/>

    <xsl:key name="projects" match="row" use="concat(col[@field='Project Name'],
                                                     col[@field='Project Code'])"/>
    <xsl:key name="statuses"
             match="row"
             use="col[@field='Status']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Lead Organisations -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('orgs',
                                                        col[@field='Lead Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName">
                        <xsl:value-of select="col[@field='Lead Organisation']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Statuses -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('statuses',
                                                        col[@field='Status'])[1])]">
                <xsl:call-template name="Status"/>
            </xsl:for-each>

            <!-- Projects -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('projects',
                                                                   concat(col[@field='Project Name'],
                                                                          col[@field='Project Code']))[1])]">
                <xsl:call-template name="Project"/>
            </xsl:for-each>

            <!-- Beneficiary Types -->
            <xsl:for-each select="//row[1]/col[starts-with(@field, 'Beneficiaries')]">
                <xsl:call-template name="BeneficiaryType"/>
            </xsl:for-each>

            <!-- Project Locations -->
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="ProjectCode" select="col[@field='Project Code']/text()"/>
        <xsl:variable name="ProjectName" select="col[@field='Project Name']/text()"/>

        <resource name="project_location">
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

            <!-- Link to Project -->
            <reference field="project_id" resource="project_project">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Project:', $ProjectCode, $ProjectName)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Location -->
            <xsl:call-template name="LocationReference"/>

            <xsl:call-template name="splitList">
                <xsl:with-param name="list">
                    <xsl:value-of select="col[@field='Activity Types']"/>
                </xsl:with-param>
                <xsl:with-param name="arg">activity_type_ref</xsl:with-param>
            </xsl:call-template>

            <xsl:call-template name="ContactPersonReference"/>

            <xsl:for-each select="col[starts-with(@field, 'Beneficiaries')]">
                <xsl:call-template name="Beneficiaries"/>
            </xsl:for-each>

        </resource>

        <xsl:call-template name="splitList">
            <xsl:with-param name="list">
                <xsl:value-of select="col[@field='Activity Types']"/>
            </xsl:with-param>
            <xsl:with-param name="arg">activity_type_res</xsl:with-param>
        </xsl:call-template>

        <xsl:call-template name="ContactPerson"/>

        <!-- Locations -->
        <xsl:call-template name="Locations"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Project">
        <xsl:variable name="ProjectCode" select="col[@field='Project Code']/text()"/>
        <xsl:variable name="ProjectName" select="col[@field='Project Name']/text()"/>
        <xsl:variable name="OrgName" select="col[@field='Lead Organisation']/text()"/>

        <resource name="project_project">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Project:', $ProjectCode, $ProjectName)"/>
            </xsl:attribute>
            <xsl:if test="$ProjectName!=''">
                <data field="name"><xsl:value-of select="$ProjectName"/></data>
            </xsl:if>
            <xsl:if test="$ProjectCode!=''">
                <data field="code"><xsl:value-of select="$ProjectCode"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Status']!=''">
                <xsl:call-template name="Status"/>
            </xsl:if>
            <!-- Project Organisations -->
            <xsl:if test="$OrgName!=''">
                <!-- Embedded within record -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Organisation:', $OrgName)"/>
                    </xsl:attribute>
                </reference>
                <!-- As link-table on Tab -->
                <resource name="project_organisation">
                    <!-- Lead Organisation -->
                    <data field="role">1</data>
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Organisation:', $OrgName)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
            <xsl:if test="col[@field='Donor Organisations']!=''">
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list">
                        <xsl:value-of select="col[@field='Donor Organisations']"/>
                    </xsl:with-param>
                    <xsl:with-param name="arg">donor</xsl:with-param>
                </xsl:call-template>
            </xsl:if>
            <xsl:if test="col[@field='Partner Organisations']!=''">
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list">
                        <xsl:value-of select="col[@field='Partner Organisations']"/>
                    </xsl:with-param>
                    <xsl:with-param name="arg">partner</xsl:with-param>
                </xsl:call-template>
            </xsl:if>
        </resource>

         <xsl:if test="col[@field='Donor Organisations']!=''">
            <xsl:call-template name="splitList">
                <xsl:with-param name="list">
                    <xsl:value-of select="col[@field='Donor Organisations']"/>
                </xsl:with-param>
                <xsl:with-param name="arg">org</xsl:with-param>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="col[@field='Partner Organisations']!=''">
            <xsl:call-template name="splitList">
                <xsl:with-param name="list">
                    <xsl:value-of select="col[@field='Partner Organisations']"/>
                </xsl:with-param>
                <xsl:with-param name="arg">org</xsl:with-param>
            </xsl:call-template>
        </xsl:if>

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
            <xsl:when test="$arg='org'">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName">$item</xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$arg='donor'">
                <resource name="project_organisation">
                    <!-- OCHA -->
                    <data field="role">3</data>
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Organisation:', $item)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>
            <xsl:when test="$arg='partner'">
                <resource name="project_organisation">
                    <!-- OCHA -->
                    <data field="role">2</data>
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Organisation:', $item)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:param name="OrgName"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Organisation:', $OrgName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Status">
        <xsl:variable name="Status" select="col[@field='Status']/text()"/>

        <resource name="project_status">
            <data field="name"><xsl:value-of select="$Status"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Beneficiaries">

        <xsl:variable name="BeneficiaryType" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="BeneficiaryNumber" select="text()"/>

        <xsl:if test="$BeneficiaryNumber!=''">
            <resource name="project_beneficiary">
                <reference field="parameter_id" resource="project_beneficiary_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('BNF:', $BeneficiaryType)"/>
                    </xsl:attribute>
                </reference>
                <data field="value"><xsl:value-of select="$BeneficiaryNumber"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="BeneficiaryType">
        <xsl:variable name="BeneficiaryType" select="normalize-space(substring-after(@field, ':'))"/>

        <resource name="project_beneficiary_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('BNF:', $BeneficiaryType)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$BeneficiaryType"/></data>
        </resource>

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
            <xsl:variable name="Email" select="substring-before(substring-after(substring-after($PersonData, ','), ','), ',')"/>
            <xsl:if test="$FirstName!='' and $Email!=''">

                <resource name="project_location_contact">
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
</xsl:stylesheet>

