<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:hrm="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Training Event - CSV Import Stylesheet

         Column headers defined in this stylesheet:
         Organisation
         Course
         Venue
         Venue Type
         Start Date
         End Date
         Comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Index for faster processing & deduplication -->
    <xsl:key name="courses" match="row" use="col[@field='Course']"/>
    <xsl:key name="organisation" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="sites" match="row" use="concat(col[@field='Venue'], '/',
                                                  col[@field='Facility Type'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation',
                                                                   col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Sites -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('sites',
                                                                   concat(col[@field='Venue'], '/',
                                                                          col[@field='Facility Type']))[1])]">
                <xsl:call-template name="Site"/>
            </xsl:for-each>

            <!-- Courses -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('courses',
                                                                   col[@field='Course'])[1])]">
                <xsl:call-template name="Course"/>
            </xsl:for-each>

            <!-- Process all table rows for event records -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="CourseName" select="col[@field='Course']/text()"/>
        <xsl:variable name="OrganisationName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="SiteName" select="col[@field='Venue']/text()"/>
        <xsl:variable name="StartDate" select="col[@field='Start Date']/text()"/>
        <xsl:variable name="EndDate" select="col[@field='End Date']/text()"/>

        <resource name="hrm_training_event">
            <xsl:if test="$CourseName!=''">
                <reference field="course_id" resource="hrm_course">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$CourseName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="$OrganisationName!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrganisationName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="$SiteName!=''">
                <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>

                <xsl:variable name="resourcename">
                    <xsl:choose>
                        <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                        <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                        <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
                        <xsl:when test="$FacilityType='Shelter'">cr_shelter</xsl:when>
                        <xsl:when test="$FacilityType='Warehouse'">inv_warehouse</xsl:when>
                        <xsl:otherwise>org_office</xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <reference field="site_id">
                    <xsl:attribute name="resource">
                        <xsl:value-of select="$resourcename"/>
                    </xsl:attribute>
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$SiteName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="$StartDate!=''">
                <data field="start_date"><xsl:value-of select="$StartDate"/></data>
            </xsl:if>
            <xsl:if test="$EndDate!=''">
                <data field="end_date"><xsl:value-of select="$EndDate"/></data>
            </xsl:if>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:variable name="OrganisationName" select="col[@field='Organisation']/text()"/>

        <xsl:if test="$OrganisationName!=''">
            <resource name="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OrganisationName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$OrganisationName"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Course">
        <xsl:variable name="CourseName" select="col[@field='Course']/text()"/>

        <xsl:if test="$CourseName!=''">
            <resource name="hrm_course">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$CourseName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$CourseName"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Site">
        <xsl:variable name="SiteName" select="col[@field='Venue']/text()"/>

        <xsl:if test="$SiteName!=''">
            <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>

            <xsl:variable name="resourcename">
                <xsl:choose>
                    <xsl:when test="$FacilityType='Office'">org_office</xsl:when>
                    <xsl:when test="$FacilityType='Facility'">org_facility</xsl:when>
                    <xsl:when test="$FacilityType='Hospital'">hms_hospital</xsl:when>
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
                    <xsl:value-of select="$SiteName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$SiteName"/></data>
                <!-- Link to Organisation. No: Leave this to deduplicator...although Offices will need creating beforehand as Organisation is mandatory for them
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='Organisation']"/>
                    </xsl:attribute>
                </reference> -->
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
