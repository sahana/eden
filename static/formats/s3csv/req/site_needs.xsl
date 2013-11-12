<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Site Needs - CSV Import Stylesheet

         CSV fields:
         Organisation............org_organisation
         Branch..................org_organisation[_branch]
         Site....................org_facility
         Time....................site_needs.time_details
         Goods...................site_needs.goods_details

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="organisation" match="row" use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Top-level Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation', col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName">
                        <xsl:value-of select="col[@field='Organisation']/text()"/>
                    </xsl:with-param>
                    <xsl:with-param name="BranchName"></xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Branch Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('branch', concat(col[@field='Organisation'], '/',
                                                                                        col[@field='Branch']))[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName"></xsl:with-param>
                    <xsl:with-param name="BranchName">
                        <xsl:value-of select="col[@field='Branch']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Needs -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Create the variables -->
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="BranchName" select="col[@field='Branch']/text()"/>
        <xsl:variable name="SiteName" select="col[@field='Site']/text()"/>

        <resource name="org_facility">
            <xsl:attribute name="tuid">
                <xsl:choose>
                    <xsl:when test="$BranchName!=''">
                        <xsl:value-of select="concat($OrgName,$BranchName,$SiteName)"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="concat($OrgName,$SiteName)"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>

            <data field="name"><xsl:value-of select="$SiteName"/></data>

            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:choose>
                        <xsl:when test="$BranchName!=''">
                            <xsl:value-of select="concat($OrgName,$BranchName)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$OrgName"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </reference>
        </resource>

        <resource name="req_site_needs">
            <!-- Link to Site -->
            <reference field="site_id" resource="org_facility">
                <xsl:attribute name="tuid">
                    <xsl:choose>
                        <xsl:when test="$BranchName!=''">
                            <xsl:value-of select="concat($OrgName,$BranchName,$SiteName)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="concat($OrgName,$SiteName)"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </reference>

            <xsl:if test="col[@field='Time']!=''">
                <data field="vol">True</data>
                <data field="vol_details"><xsl:value-of select="col[@field='Time']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Goods']!=''">
                <data field="goods">True</data>
                <data field="goods_details"><xsl:value-of select="col[@field='Goods']"/></data>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:param name="OrgName"/>
        <xsl:param name="BranchName"/>

        <xsl:choose>
            <xsl:when test="$BranchName!=''">
                <!-- This is the Branch -->
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat(col[@field='Organisation'],$BranchName)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$BranchName"/></data>
                    <!-- Don't create Orgs as Branches of themselves -->
                    <xsl:if test="col[@field='Organisation']!=$BranchName">
                        <resource name="org_organisation_branch" alias="parent">
                            <reference field="organisation_id" resource="org_organisation">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="col[@field='Organisation']"/>
                                </xsl:attribute>
                            </reference>
                        </resource>
                    </xsl:if>
                </resource>
            </xsl:when>
            <xsl:when test="$OrgName!=''">
                <!-- This is the top-level Organisation -->
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$OrgName"/></data>
                </resource>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
