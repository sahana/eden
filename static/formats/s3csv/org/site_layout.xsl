<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Site Locations - CSV Import Stylesheet

         CSV fields:
         Facility.............................org_site.name
         Facility Type........................org_site.instance_type
         Name.................................org_site_layout.name
         Parent...............................org_site_layout.parent$name
         Grandparent..........................org_site_layout.parent$parent$name

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="site" match="row" use="col[@field='Facility']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>

            <!-- Sites -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('site',
                                                                       col[@field='Facility'])[1])]">
                <xsl:call-template name="Site"/>
            </xsl:for-each>

            <!-- Site Layouts -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="SiteName" select="col[@field='Facility']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>
        <xsl:variable name="resourcename">
            <xsl:choose>
                <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                <xsl:when test="$FacilityType='Fire Station'">fire_station</xsl:when>
                <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                <xsl:when test="$FacilityType='Police Station'">police_station</xsl:when>
                <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                <xsl:otherwise>org_office</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="Name" select="col[@field='Name']/text()"/>
        <xsl:variable name="Parent" select="col[@field='Parent']/text()"/>
        <xsl:variable name="Grandparent" select="col[@field='Grandparent']/text()"/>

        <!-- Site Layout -->
        <resource name="org_site_layout">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($SiteName, '/', $Name, '/', $Parent, '/', $Grandparent)"/>
            </xsl:attribute>

            <data field="name"><xsl:value-of select="$Name"/></data>

            <!-- Facility -->
            <reference field="site_id">
                <xsl:attribute name="resource">
                    <xsl:value-of select="$resourcename"/>
                </xsl:attribute>
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Site:', $SiteName)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to parent node (if any) -->
            <xsl:if test="$Parent!=''">
                <reference field="parent" resource="org_site_layout">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($SiteName, '/', $Parent, '/', $Grandparent, '/')"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Site">

        <xsl:variable name="SiteName" select="col[@field='Facility']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>

        <xsl:variable name="resourcename">
            <xsl:choose>
                <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                <xsl:when test="$FacilityType='Fire Station'">fire_station</xsl:when>
                <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                <xsl:when test="$FacilityType='Police Station'">police_station</xsl:when>
                <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                <xsl:otherwise>org_office</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <resource>
            <xsl:attribute name="name">
                <xsl:value-of select="$resourcename"/>
            </xsl:attribute>
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Site:', $SiteName)"/>
                <!-- <xsl:call-template name="OrganisationID">
                    <xsl:with-param name="prefix">OFFICE:</xsl:with-param>
                    <xsl:with-param name="suffix" select="concat('/', $SiteName)"/>
                </xsl:call-template> -->
            </xsl:attribute>

            <!-- Name field is limited to 64 chars -->
            <data field="name"><xsl:value-of select="substring($SiteName,1,64)"/></data>

            <!-- Link to Organisation
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:call-template name="OrganisationID"/>
                </xsl:attribute>
            </reference> -->
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
