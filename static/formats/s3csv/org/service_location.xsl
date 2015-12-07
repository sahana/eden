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
    <!-- Indexes for faster processing -->

    <!-- Organisations and Branches -->
    <xsl:key name="organisations" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="branches" match="row"
             use="concat(col[@field='Organisation'], '/', col[@field='Branch'])"/>

    <!-- Sites -->
    <xsl:key name="sites" match="row"
             use="concat(col[@field='Site Name'], '/', col[@field='Site Type'])"/>

    <!-- Locations -->
    <!-- @todo -->

    <!-- ****************************************************************** -->
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

            <!-- Create Locations -->
            <!-- @todo -->

            <!-- Service Locations -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Create Service Types -->
        <xsl:call-template name="ServiceTypes">
            <xsl:with-param name="list">
                <xsl:value-of select="col[@field='Services']/text()"/>
            </xsl:with-param>
        </xsl:call-template>

        <resource name="org_service_location">

            <!-- Link to organisation -->
            <xsl:call-template name="OrganisationLink"/>

            <xsl:choose>
                <!-- Link to site (if present) -->
                <xsl:when test="col[@field='Site Name']/text()!='' and
                                col[@field='Site Type']/text()!=''">
                    <xsl:call-template name="SiteLink"/>
                </xsl:when>

                <!-- Link to location (if present and not site) -->
                <!-- @todo -->

                <!-- Simple location name (of present and neither site nor location) -->
                <!-- @todo -->
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

            <!-- Create Service Type Links -->
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
            <xsl:choose>
                <xsl:when test="$SiteType='OFFICE'">org_office</xsl:when>
                <xsl:when test="$SiteType='SHELTER'">cr_shelter</xsl:when>
                <xsl:otherwise>org_facility</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$resource!='' and $tuid!=''">
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
                <!-- @todo: link to location if present -->
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

</xsl:stylesheet>
