<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Job Titles - CSV Import Stylesheet

         CSV fields:
         Name............................hrm_job_title.name
         Type............................hrm_job_title.type
         Organisation....................hrm_job_title.organisation_id
         Region..........................hrm_job_title.region_id
         Comments........................hrm_job_title.comments

    *********************************************************************** -->
    <xsl:import href="../commons.xsl"/>

    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="regions" match="row" use="col[@field='Region']"/>
    <xsl:key name="orgs" match="row" use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Regions -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('regions',
                                                                       col[@field='Region'])[1])]">
                <xsl:call-template name="Region"/>
            </xsl:for-each>

            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('orgs',
                                                                       col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="RegionName" select="col[@field='Region']/text()"/>
        <xsl:variable name="Type">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string" select="col[@field='Type']/text()"/>
            </xsl:call-template>
        </xsl:variable>

        <!-- HRM Job Title -->
        <resource name="hrm_job_title">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

            <xsl:choose>
                <xsl:when test="$Type='1' or $Type='STAFF'">
                    <data field="type">1</data>
                </xsl:when>
                <xsl:when test="$Type='2' or $Type='VOLUNTEER' or $Type='VOL'">
                    <data field="type">2</data>
                </xsl:when>
                <xsl:when test="$Type='4' or $Type='DEPLOY' or $Type='RDRT'">
                    <data field="type">4</data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Default -->
                </xsl:otherwise>
            </xsl:choose>

            <!-- Link to Organisation to filter lookup lists -->
            <xsl:if test="$OrgName!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Link to Region to filter lookup lists -->
            <xsl:if test="$RegionName!=''">
                <reference field="region_id" resource="org_region">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$RegionName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Region">

        <xsl:variable name="RegionName" select="col[@field='Region']/text()"/>

        <resource name="org_region">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$RegionName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$RegionName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
