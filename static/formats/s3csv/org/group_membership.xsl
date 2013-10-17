<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Organisation Groups - CSV Import Stylesheet

         CSV fields:
         Group...........................org_group.name
         Organisation....................org_organisation.name

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="group" match="row" use="col[@field='Group']"/>
    <xsl:key name="org" match="row" use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Groups -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('group',
                                                                       col[@field='Group'])[1])]">
                <xsl:call-template name="Group"/>
            </xsl:for-each>

            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('org',
                                                                       col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Memberships -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="GroupName" select="col[@field='Group']"/>
        <xsl:variable name="OrgName" select="col[@field='Organisation']"/>

        <resource name="org_group_membership">
            <reference field="group_id" resource="org_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Group:', $GroupName)"/>
                </xsl:attribute>
            </reference>
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Org:', $OrgName)"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Group">
        <xsl:variable name="GroupName" select="col[@field='Group']"/>

        <resource name="org_group">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Group:', $GroupName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$GroupName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:variable name="OrgName" select="col[@field='Organisation']"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Org:', $OrgName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
