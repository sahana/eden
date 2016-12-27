<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
        Service Locations - CSV Import Stylesheet

        CSV fields:

        Organisation................Organisation Name (mandatory)
        Branch......................Organisation Branch Name
        Site Name...................Name of the Site
        Site Type...................Site Type
                                    OFFICE|SHELTER|FACILITY
        Country.....................Country Name
        Building....................Building Name
        Address.....................Street Address
        Postcode....................Postcode
        L1,L2,L3,L4,L5..............Administrative Area Names (Hierarchy)
        Lat.........................Latitude
        Lon.........................Longitude
        Location....................Location Name
                                    (as alternative to site/location data)
        Description.................Service Location Description
        Start Date..................Start Date
        End Date....................End Date
        Status......................Status Code
                                    PLANNED|ACTIVE|SUSPENDED|DISCONTINUED
        Services....................List of service type names, separated by |
        Comments....................Comments

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

    <xsl:variable name="Postcode">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Postcode</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->

    <!-- Organisations and Branches -->
    <xsl:key name="organisations" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="branches" match="row"
             use="concat(col[@field='Organisation'], '/', col[@field='Branch'])"/>

    <!-- Sites -->
    <xsl:key name="sites" match="row"
             use="concat(col[@field='Site Name'], '/', col[@field='Site Type'])"/>

    <!-- Administrative Areas -->
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
    <!-- Root template -->

    <xsl:template match="/">
        <s3xml>

            <!-- Create Organisations and Branches -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisations',
                                                                       col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName">
                        <xsl:value-of select="col[@field='Organisation']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <xsl:for-each select="//row[generate-id(.)=generate-id(key('branches',
                                                                       concat(col[@field='Organisation'], '/',
                                                                              col[@field='Branch']))[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName">
                        <xsl:value-of select="col[@field='Organisation']/text()"/>
                    </xsl:with-param>
                    <xsl:with-param name="BranchName">
                        <xsl:value-of select="col[@field='Branch']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Create Sites -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('sites',
                                                                       concat(col[@field='Site Name'], '/',
                                                                              col[@field='Site Type']))[1])]">
                <xsl:call-template name="Site"/>
            </xsl:for-each>

            <!-- Create Administrative Areas -->

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

            <!-- Service Locations -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Service Locations -->

    <xsl:template match="row">

        <!-- Get the site name (falls back to "Location" column) -->
        <xsl:variable name="SiteName">
            <xsl:choose>
                <xsl:when test="col[@field='Site Name']/text()!=''">
                    <xsl:value-of select="col[@field='Site Name']/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="col[@field='Location']/text()"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <!-- Location data -->
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="l5" select="col[@field='L5']/text()"/>
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
        <xsl:variable name="postcode">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Postcode"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="address" select="col[@field='Address']/text()"/>

        <!-- Convert l0 into country code = UUID of the L0 location -->
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

        <!-- Create specific location if data present -->
        <xsl:if test="$SiteName!='' or $lat!='' and $lon!='' or $address!='' or $postcode!=''">
            <xsl:call-template name="Locations">
                <xsl:with-param name="SiteName">
                    <xsl:if test="$SiteName!=''">
                        <xsl:value-of select="$SiteName"/>
                    </xsl:if>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>

        <!-- Create Service Types -->
        <xsl:call-template name="ServiceTypes">
            <xsl:with-param name="list">
                <xsl:value-of select="col[@field='Services']/text()"/>
            </xsl:with-param>
        </xsl:call-template>

        <!-- Create the Service Location -->
        <resource name="org_service_location">

            <!-- Link to the organisation -->
            <xsl:call-template name="OrganisationLink"/>

            <!-- Link to location (alternatives) -->
            <xsl:choose>

                <!-- Link to site -->
                <xsl:when test="col[@field='Site Name']/text()!='' and
                                col[@field='Site Type']/text()!=''">
                    <xsl:call-template name="SiteLink"/>
                </xsl:when>

                <!-- 1st alternative: link to specific location -->
                <xsl:when test="$SiteName!='' or $lat!='' and $lon!='' or $address!='' or $postcode!=''">
                    <!-- Specific location -->
                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:choose>
                                <xsl:when test="$SiteName!=''">
                                    <xsl:value-of select="concat('LOCATION:', $SiteName)"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:value-of select="concat('LOCATION-', position())"/>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:attribute>
                    </reference>
                </xsl:when>

                <!-- 2nd alternative: link to administrative area -->
                <xsl:when test="$l5!=''">
                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l4!=''">
                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l3!=''">
                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l2!=''">
                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l1!=''">
                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l0!=''">
                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$country"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>

                <!-- Fallback: simple location name -->
                <xsl:when test="$SiteName!=''">
                    <data field="location"><xsl:value-of select="$SiteName"/></data>
                </xsl:when>

            </xsl:choose>

            <!-- Description -->
            <xsl:variable name="Description" select="col[@field='Description']/text()"/>
            <xsl:if test="$Description!=''">
                <data field="description">
                    <xsl:value-of select="$Description"/>
                </data>
            </xsl:if>

            <!-- Start Date -->
            <xsl:variable name="StartDate" select="col[@field='Start Date']/text()"/>
            <xsl:if test="$StartDate!=''">
                <data field="start_date">
                    <xsl:value-of select="$StartDate"/>
                </data>
            </xsl:if>

            <!-- End Date -->
            <xsl:variable name="EndDate" select="col[@field='End Date']/text()"/>
            <xsl:if test="$EndDate!=''">
                <data field="end_date">
                    <xsl:value-of select="$EndDate"/>
                </data>
            </xsl:if>

            <!-- Service Type Links -->
            <xsl:call-template name="ServiceTypeLinks">
                <xsl:with-param name="list">
                    <xsl:value-of select="col[@field='Services']/text()"/>
                </xsl:with-param>
            </xsl:call-template>

            <!-- Status -->
            <xsl:call-template name="ServiceLocationStatus"/>

            <!-- Comments -->
            <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>
            <xsl:if test="$Comments!=''">
                <data field="comments">
                    <xsl:value-of select="$Comments"/>
                </data>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Service Location Status -->

    <xsl:template name="ServiceLocationStatus">

        <xsl:variable name="StatusText" select="col[@field='Status']/text()"/>

        <xsl:if test="$StatusText!=''">

            <xsl:variable name="StatusCode">
                <xsl:call-template name="uppercase">
                    <xsl:with-param name="string">
                        <xsl:value-of select="$StatusText"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:variable>

            <xsl:variable name="Status">
                <xsl:choose>
                    <xsl:when test="$StatusCode='PLANNED'">PLANNED</xsl:when>
                    <xsl:when test="$StatusCode='ACTIVE'">ACTIVE</xsl:when>
                    <xsl:when test="$StatusCode='SUSPENDED'">SUSPENDED</xsl:when>
                    <xsl:when test="$StatusCode='DISCONTINUED'">DISCONTINUED</xsl:when>
                    <xsl:otherwise>ACTIVE</xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:if test="$Status!=''">
                <data field="status">
                    <xsl:value-of select="$Status"/>
                </data>
            </xsl:if>

        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Organisation or Branch (from index) -->

    <xsl:template name="Organisation">

        <xsl:param name="OrgName"/>
        <xsl:param name="BranchName"/>

        <xsl:variable name="tuid">
            <xsl:choose>
                <xsl:when test="$OrgName!='' and $BranchName!=''">
                    <xsl:value-of select="concat('ORG:', $OrgName, ':', $BranchName)"/>
                </xsl:when>
                <xsl:when test="$OrgName!=''">
                    <xsl:value-of select="concat('ORG:', $OrgName)"/>
                </xsl:when>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="parent">
            <xsl:if test="$OrgName!='' and $BranchName!='' and $OrgName!=$BranchName">
                <xsl:value-of select="concat('ORG:', $OrgName)"/>
            </xsl:if>
        </xsl:variable>

        <resource name="org_organisation">

            <xsl:attribute name="tuid">
                <xsl:value-of select="$tuid"/>
            </xsl:attribute>

            <data field="name">
                <xsl:choose>
                    <xsl:when test="$BranchName!=''">
                        <xsl:value-of select="$BranchName"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$OrgName"/>
                    </xsl:otherwise>
                </xsl:choose>
            </data>

            <xsl:if test="$parent!=''">
                <resource name="org_organisation_branch" alias="parent">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$parent"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Link Service Location <=> Organisation -->

    <xsl:template name="OrganisationLink">

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="BranchName" select="col[@field='Branch']/text()"/>

        <xsl:variable name="tuid">
            <xsl:choose>
                <xsl:when test="$OrgName!='' and $BranchName!=''">
                    <xsl:value-of select="concat('ORG:', $OrgName, ':', $BranchName)"/>
                </xsl:when>
                <xsl:when test="$OrgName!=''">
                    <xsl:value-of select="concat('ORG:', $OrgName)"/>
                </xsl:when>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$tuid!=''">
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$tuid"/>
                </xsl:attribute>
            </reference>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Site (from index) -->

    <xsl:template name="Site">

        <xsl:variable name="SiteName" select="col[@field='Site Name']/text()"/>
        <xsl:variable name="SiteType" select="col[@field='Site Type']/text()"/>

        <xsl:variable name="tuid">
            <xsl:if test="$SiteName!='' and $SiteType!=''">
                <xsl:value-of select="concat('SITE:', $SiteType, ':', $SiteName)"/>
            </xsl:if>
        </xsl:variable>

        <xsl:variable name="resource">
            <!-- @todo: add other site types (warehouses, hospitals) -->
            <xsl:choose>
                <xsl:when test="$SiteType='OFFICE'">org_office</xsl:when>
                <xsl:when test="$SiteType='SHELTER'">cr_shelter</xsl:when>
                <xsl:otherwise>org_facility</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$resource!='' and $tuid!=''">

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
            <xsl:variable name="postcode">
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$Postcode"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="address" select="col[@field='Address']/text()"/>

            <resource>
                <xsl:attribute name="name">
                    <xsl:value-of select="$resource"/>
                </xsl:attribute>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$tuid"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="$SiteName"/>
                </data>
                <xsl:if test="$lat!='' and $lon!='' or $postcode!='' or $address!=''">
                    <!-- Specific location exists for this row, link the site to it -->
                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('LOCATION:', $SiteName)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
                <xsl:if test="$resource='org_office'">
                    <!-- Organisation is required for offices -->
                    <xsl:call-template name="OrganisationLink"/>
                </xsl:if>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Link Service Location <=> Site -->

    <xsl:template name="SiteLink">

        <xsl:variable name="SiteName" select="col[@field='Site Name']/text()"/>
        <xsl:variable name="SiteType" select="col[@field='Site Type']/text()"/>

        <xsl:variable name="tuid">
            <xsl:if test="$SiteName!='' and $SiteType!=''">
                <xsl:value-of select="concat('SITE:', $SiteType, ':', $SiteName)"/>
            </xsl:if>
        </xsl:variable>

        <xsl:variable name="resource">
            <xsl:choose>
                <xsl:when test="$SiteType='OFFICE'">org_office</xsl:when>
                <xsl:when test="$SiteType='SHELTER'">cr_shelter</xsl:when>
                <xsl:otherwise>org_facility</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$resource!='' and $tuid!=''">
            <reference field="site_id">
                <xsl:attribute name="resource">
                    <xsl:value-of select="$resource"/>
                </xsl:attribute>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$tuid"/>
                </xsl:attribute>
            </reference>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Service Types -->

    <xsl:template name="ServiceTypes">

        <xsl:param name="list"/>

        <xsl:variable name="head">
            <xsl:choose>
                <xsl:when test="contains($list, '|')">
                    <xsl:value-of select="substring-before($list, '|')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$list"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="tail" select="substring-after($list, '|')"/>

        <xsl:if test="$head!='' and
                      not(preceding-sibling::row[contains(concat('|', col[@field='Services'], '|'), $head)])">
            <resource name="org_service">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('SERVICE:', $head)"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="$head"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="$tail!=''">
            <xsl:call-template name="ServiceTypes">
                <xsl:with-param name="list">
                    <xsl:value-of select="$tail"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Links Service Location <=> Service Types -->

    <xsl:template name="ServiceTypeLinks">

        <xsl:param name="list"/>

        <xsl:variable name="head">
            <xsl:choose>
                <xsl:when test="contains($list, '|')">
                    <xsl:value-of select="substring-before($list, '|')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$list"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="tail" select="substring-after($list, '|')"/>

        <xsl:if test="$head!=''">
            <resource name="org_service_location_service">
                <reference field="service_id" resource="org_service">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('SERVICE:', $head)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

        <xsl:if test="$tail!=''">
            <xsl:call-template name="ServiceTypeLinks">
                <xsl:with-param name="list">
                    <xsl:value-of select="$tail"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- L1 Administrative Area -->

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
    <!-- L2 Administrative Area -->

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
    <!-- L3 Administrative Area -->

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

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

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
    <!-- L4 Administrative Area -->

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

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

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
    <!-- L5 Administrative Area -->

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
    <!-- Specific Location -->

    <xsl:template name="Locations">

        <xsl:param name="SiteName"/>

        <!-- Location Data -->
        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="l5" select="col[@field='L5']/text()"/>
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
        <xsl:variable name="postcode">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Postcode"/>
            </xsl:call-template>
        </xsl:variable>
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

        <!-- Create specific location -->
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:choose>
                    <xsl:when test="$SiteName!=''">
                        <xsl:value-of select="concat('LOCATION:', $SiteName)"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="concat('LOCATION-', position())"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="$l5!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L5/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4, '/', $l5)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l4!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l3!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l2!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l1!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:otherwise>
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="$Building!=''">
                    <data field="name"><xsl:value-of select="$Building"/></data>
                </xsl:when>
                <xsl:otherwise>
                    <data field="name"><xsl:value-of select="$SiteName"/></data>
                </xsl:otherwise>
            </xsl:choose>
            <data field="addr_street"><xsl:value-of select="col[@field='Address']"/></data>
            <data field="addr_postcode"><xsl:value-of select="$postcode"/></data>
            <data field="lat"><xsl:value-of select="$lat"/></data>
            <data field="lon"><xsl:value-of select="$lon"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
