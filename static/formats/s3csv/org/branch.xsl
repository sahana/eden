<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Organisation Branches - CSV Import Stylesheet

         CSV fields:
         Organisation............org_organisation (the master org's name)
         Branch..................org_organisation (the branch org's name)

         If "Organisation" is empty, the branch will be created as independent
         organisation, so this can also be used as generic organisation import
         stylesheet.

         all of the following are for the branch:
         Acronym.................org_organisation
         Type....................org_organisation
         Sector..................org_sector
         Region..................org_organisation
         Country.................org_organisation (ISO Code)
         Website.................org_organisation
         Twitter.................org_organisation
         Donation Phone..........org_organisation
         Comments................org_organisation

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="./organisation.xsl"/>
    <xsl:key name="organisation" match="row" use="col[@field='Organisation']"/>

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation', col[@field='Organisation'])[1])]">
                <xsl:variable name="OrganisationName" select="col[@field='Organisation']"/>
                <xsl:if test="$OrganisationName!=''">
                    <xsl:if test="not(//row/col[@field='Branch']=$OrganisationName)">
                        <xsl:call-template name="Organisation">
                            <xsl:with-param name="OrganisationName"></xsl:with-param>
                            <xsl:with-param name="BranchName"><xsl:value-of select="$OrganisationName"/></xsl:with-param>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:if>
            </xsl:for-each>
        </s3xml>
    </xsl:template>

    <xsl:template match="row">
        <xsl:variable name="OrganisationName" select="col[@field='Organisation']"/>
        <xsl:variable name="BranchName" select="col[@field='Branch']"/>

        <xsl:call-template name="Organisation">
            <xsl:with-param name="OrganisationName"><xsl:value-of select="$OrganisationName"/></xsl:with-param>
            <xsl:with-param name="BranchName"><xsl:value-of select="$BranchName"/></xsl:with-param>
        </xsl:call-template>
    </xsl:template>

    <xsl:template name="Organisation">

        <xsl:param name="OrganisationName"/>
        <xsl:param name="BranchName"/>

        <!-- Create the sectors -->
        <xsl:variable name="sector" select="col[@field='Sector']"/>
        <xsl:call-template name="splitList">
            <xsl:with-param name="list" select="$sector"/>
        </xsl:call-template>

        <!-- Create the Organisation -->
        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$BranchName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$BranchName"/></data>
            <data field="acronym"><xsl:value-of select="col[@field='Acronym']"/></data>

            <xsl:variable name="typename" select="col[@field='Type']"/>
            <xsl:variable name="typecode" select="document('')//org:type[text()=normalize-space($typename)]/@code"/>
            <xsl:if test="$typecode">
                <data field="type"><xsl:value-of select="$typecode"/></data>
            </xsl:if>

            <data field="country">
                <xsl:value-of select="col[@field='Country']"/>
                <!--<xsl:call-template name="iso2countryname">
                    <xsl:with-param name="country" select="col[@field='country']"/>
                </xsl:call-template>-->
            </data>
            <data field="region"><xsl:value-of select="col[@field='Region']"/></data>
            <data field="website"><xsl:value-of select="col[@field='Website']"/></data>
            <data field="twitter"><xsl:value-of select="col[@field='Twitter']"/></data>
            <data field="donation_phone"><xsl:value-of select="col[@field='Donation Phone']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

            <reference field="sector_id" resource="org_sector">
                <xsl:variable name="qlist">
                    <xsl:call-template name="quoteList">
                        <xsl:with-param name="list" select="$sector"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('[', $qlist, ']')"/>
                </xsl:attribute>
            </reference>

            <xsl:for-each select="//row[col[@field='Organisation']=$BranchName]">
                <resource name="org_organisation_branch">
                    <reference field="branch_id">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='Branch']"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:for-each>
        </resource>

    </xsl:template>

</xsl:stylesheet>
