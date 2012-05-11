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

    <xsl:include href="../../xml/countries.xsl"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- Organisation types, see modules/eden/org.py -->
    <org:type code="1">Government</org:type>
    <org:type code="2">Embassy</org:type>
    <org:type code="3">International NGO</org:type>
    <org:type code="4">Donor</org:type>
    <org:type code="6">National NGO</org:type>
    <org:type code="7">UN</org:type>
    <org:type code="8">International Organization</org:type>
    <org:type code="9">Military</org:type>
    <org:type code="10">Private</org:type>
    <org:type code="11">Intergovernmental Organization</org:type>
    <org:type code="12">Institution</org:type>
    <org:type code="13">Red Cross / Red Crescent</org:type>

    <!-- Indexes for faster processing -->
    <xsl:key name="organisation" match="row" use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Branches -->
            <xsl:apply-templates select="table/row"/>

            <!-- Top-level Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation', col[@field='Organisation'])[1])]">
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

            <xsl:if test="col[@field='Acronym']!=''">
                <data field="acronym"><xsl:value-of select="col[@field='Acronym']"/></data>
            </xsl:if>
            
            <xsl:variable name="typename" select="col[@field='Type']"/>
            <xsl:if test="$typename!=''">
                <xsl:variable name="typecode" select="document('')//org:type[text()=normalize-space($typename)]/@code"/>
                <xsl:if test="$typecode">
                    <data field="type"><xsl:value-of select="$typecode"/></data>
                </xsl:if>
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
            </xsl:if>

            <xsl:if test="$OrgName!=''">
                <!-- Nest all the Branches -->
                <xsl:for-each select="//row[col[@field='Organisation']=$OrgName]">
                    <xsl:if test="col[@field='Branch']!=''">
                        <resource name="org_organisation_branch">
                            <reference field="branch_id">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="concat($OrgName,col[@field='Branch'])"/>
                                </xsl:attribute>
                            </reference>
                        </resource>
                    </xsl:if>
                </xsl:for-each>
            </xsl:if>

        </resource>

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
