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
         Acronym.................org_organisation
         Type....................org_organisation_type
         Sector..................org_sector
         Region..................org_organisation
         Country.................org_organisation (ISO Code)
         Website.................org_organisation
         Twitter.................org_organisation
         Donation Phone..........org_organisation
         Comments................org_organisation
         Approved................org_organisation.approved_by

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/countries.xsl"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- Indexes for faster processing -->
    <xsl:key name="organisation_type" match="row" use="col[@field='Type']"/>
    <xsl:key name="organisation" match="row" use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Organisation Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation_type',
                                                                       col[@field='Type'])[1])]">
                <xsl:call-template name="OrganisationType" />
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

        <!-- Create the sectors -->
        <xsl:variable name="sector" select="col[@field='Sector']"/>
        <xsl:call-template name="splitList">
            <xsl:with-param name="list" select="$sector"/>
        </xsl:call-template>

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
                <data field="country">
                    <xsl:value-of select="col[@field='Country']"/>
                    <!--<xsl:call-template name="iso2countryname">
                        <xsl:with-param name="country" select="col[@field='country']"/>
                    </xsl:call-template>-->
                </data>
            </xsl:if>
            <xsl:if test="col[@field='Region']!=''">
                <data field="region"><xsl:value-of select="col[@field='Region']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Website']!=''">
                <data field="website"><xsl:value-of select="col[@field='Website']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Twitter']!=''">
                <data field="twitter"><xsl:value-of select="col[@field='Twitter']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Donation Phone']!=''">
                <data field="donation_phone"><xsl:value-of select="col[@field='Donation Phone']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>

            <xsl:if test="$sector!=''">
                <reference field="multi_sector_id" resource="org_sector">
                    <xsl:variable name="qlist">
                        <xsl:call-template name="quoteList">
                            <xsl:with-param name="list" select="$sector"/>
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('[', $qlist, ']')"/>
                    </xsl:attribute>
                </reference>
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
    <!-- Template to create an org_sector resource from the value passed in -->
    <xsl:template name="resource">
        <xsl:param name="item"/>

        <resource name="org_sector">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$item"/>
            </xsl:attribute>
            <data field="abrv"><xsl:value-of select="$item"/></data>
            <data field="name"><xsl:value-of select="$item"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
