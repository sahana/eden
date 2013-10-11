<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Organisation - CSV Import Stylesheet

         CSV fields:
         Organisation............org_organisation (the master org's name)
         Branch..................org_organisation (the branch org's name)

         all of the following are for the branch, unless the branch field is empty:
         Acronym.................org_organisation.acronym
         Type....................org_organisation$organisation_type_id
         Sectors.................org_sector_organisation$sector_id
         Services................org_service_organisation$service_id
         Region..................org_organisation.region_id
         Country.................org_organisation.country (ISO Code)
         Website.................org_organisation.website
         Phone...................org_organisation.phone
         Phone2..................pr_contact.value
         Twitter.................pr_contact.value
         Logo....................org_organisation.logo
         Comments................org_organisation.comments
         Approved................org_organisation.approved_by

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/countries.xsl"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="organisation_type" match="row" use="col[@field='Type']"/>
    <xsl:key name="organisation" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="region" match="row" use="col[@field='Region']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Organisation Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation_type',
                                                                       col[@field='Type'])[1])]">
                <xsl:call-template name="OrganisationType" />
            </xsl:for-each>

            <!-- Regions -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('region',
                                                                       col[@field='Region'])[1])]">
                <xsl:call-template name="Region" />
            </xsl:for-each>

            <!-- Branches -->
            <xsl:apply-templates select="table/row"/>

            <!-- Top-level Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation',
                                                                       col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName">
                        <xsl:value-of select="col[@field='Organisation']/text()"/>
                    </xsl:with-param>
                    <xsl:with-param name="BranchName"></xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="BranchName" select="col[@field='Branch']/text()"/>

        <!-- Create the Branches -->
        <xsl:if test="$BranchName!=''">
            <xsl:call-template name="Organisation">
                <xsl:with-param name="OrgName"></xsl:with-param>
                <xsl:with-param name="BranchName">
                    <xsl:value-of select="$BranchName"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:param name="OrgName"/>
        <xsl:param name="BranchName"/>

        <xsl:variable name="Sectors" select="col[@field='Sectors']/text()"/>
        <xsl:variable name="Services" select="col[@field='Services']/text()"/>

        <!-- Create the Organisation/Branch -->
        <resource name="org_organisation">
            <xsl:choose>
                <xsl:when test="$OrgName!=''">
                    <!-- This is the Organisation -->
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$OrgName"/></data>
                </xsl:when>
                <xsl:when test="$BranchName!=''">
                    <!-- This is the Branch -->
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat(col[@field='Organisation'],$BranchName)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$BranchName"/></data>
                </xsl:when>
            </xsl:choose>

            <xsl:if test="col[@field='Approved']!=''">
                <data field="approved_by">0</data>
            </xsl:if>
            
            <xsl:if test="col[@field='Acronym']!=''">
                <data field="acronym"><xsl:value-of select="col[@field='Acronym']"/></data>
            </xsl:if>
            
            <xsl:if test="col[@field='Type']!=''">
                <reference field="organisation_type_id" resource="org_organisation_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('OrgType:', col[@field='Type'])"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <xsl:if test="col[@field='Country']!=''">
                <xsl:variable name="l0">
                    <xsl:value-of select="col[@field='Country']"/>
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
                            <xsl:value-of select="$l0"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <data field="country">
                    <xsl:value-of select="$countrycode"/>
                </data>
            </xsl:if>
            <xsl:if test="col[@field='Region']!=''">
                <reference field="region_id" resource="org_region">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Region:', col[@field='Region'])"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="col[@field='Website']!=''">
                <data field="website"><xsl:value-of select="col[@field='Website']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Phone']!=''">
                <data field="phone"><xsl:value-of select="col[@field='Phone']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Phone2']!=''">
                <resource name="pr_contact">
                    <data field="contact_method">WORK_PHONE</data>
                    <data field="value"><xsl:value-of select="col[@field='Phone2']"/></data>
                </resource>
            </xsl:if>
            <xsl:if test="col[@field='Twitter']!=''">
                <resource name="pr_contact">
                    <data field="contact_method">TWITTER</data>
                    <data field="value"><xsl:value-of select="col[@field='Twitter']"/></data>
                </resource>
            </xsl:if>
            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>

            <xsl:if test="$Sectors!=''">
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list" select="$Sectors"/>
                    <xsl:with-param name="arg">sector</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <xsl:if test="$Services!=''">
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list" select="$Services"/>
                    <xsl:with-param name="arg">service</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <!-- Logo -->
            <xsl:if test="col[@field='Logo']!=''">
                <xsl:variable name="logo">
                    <xsl:value-of select="col[@field='Logo']"/>
                </xsl:variable>
                <data field="logo">
                    <xsl:attribute name="url">
                        <xsl:value-of select="$logo"/>
                    </xsl:attribute>
                    <!--
                    <xsl:attribute name="filename">
                        <xsl:call-template name="substringAfterLast">
                            <xsl:with-param name="input" select="$logo"/>
                            <xsl:with-param name="sep" select="'/'"/>
                        </xsl:call-template>
                    </xsl:attribute>-->
                </data>
            </xsl:if>

            <xsl:if test="$OrgName!=''">
                <!-- Nest all the Branches -->
                <xsl:for-each select="//row[col[@field='Organisation']=$OrgName]">
                    <xsl:if test="col[@field='Branch']!=''">
                        <!-- Don't create Orgs as Branches of themselves -->
                        <xsl:if test="col[@field='Branch']!=$OrgName">
                            <resource name="org_organisation_branch" alias="branch">
                                <reference field="branch_id"  resource="org_organisation">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="concat($OrgName,col[@field='Branch'])"/>
                                    </xsl:attribute>
                                </reference>
                            </resource>
                        </xsl:if>
                    </xsl:if>
                </xsl:for-each>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="OrganisationType">
        <xsl:if test="col[@field='Type']!=''">
            <resource name="org_organisation_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('OrgType:', col[@field='Type'])"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="col[@field='Type']"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Region">
        <xsl:if test="col[@field='Region']!=''">
            <resource name="org_region">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Region:', col[@field='Region'])"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="col[@field='Region']"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>

        <xsl:choose>
            <!-- Sectors -->
            <xsl:when test="$arg='sector'">
                <resource name="org_sector_organisation">
                    <reference field="sector_id" resource="org_sector">
                        <resource name="org_sector">
                            <data field="abrv"><xsl:value-of select="$item"/></data>
                            <data field="name"><xsl:value-of select="$item"/></data>
                        </resource>
                    </reference>
                </resource>
            </xsl:when>
            <!-- Services -->
            <xsl:when test="$arg='service'">
                <resource name="org_service_organisation">
                    <reference field="service_id" resource="org_service">
                        <resource name="org_service">
                            <data field="name"><xsl:value-of select="$item"/></data>
                        </resource>
                    </reference>
                </resource>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
