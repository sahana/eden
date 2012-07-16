<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:hrm="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Training Event Participant List - CSV Import Stylesheet

         Column headers defined in this stylesheet:
         Course,Organisation,Facility,Start,End,Hours,First Name,Last Name,Sex,Email

         Column headers looked up in labels.xml:

         PersonGender...................optional.....person gender

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="./person.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Index for faster processing & deduplication -->
    <xsl:key name="courses" match="row" use="col[@field='Course']"/>
    <xsl:key name="organisations" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="sites" match="row" use="col[@field='Facility']"/>
    <xsl:key name="persons" match="row" use="concat(col[@field='First Name'], '/',
                                                    col[@field='Last Name'], '/',
                                                    col[@field='Email'])"/>
    <xsl:key name="events" match="row" use="concat(col[@field='Facility'], '/',
                                                   col[@field='Course'], '/',
                                                   col[@field='Start'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisations',
                                                                   col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Sites -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('sites',
                                                                   col[@field='Facility'])[1])]">
                <xsl:call-template name="Site"/>
            </xsl:for-each>

            <!-- Courses -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('courses',
                                                                   col[@field='Course'])[1])]">
                <xsl:call-template name="Course"/>
            </xsl:for-each>

            <!-- Events -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('events',
                                                        concat(col[@field='Facility'], '/',
                                                               col[@field='Course'], '/',
                                                               col[@field='Start']))[1])]">
                <xsl:call-template name="Event"/>
            </xsl:for-each>

            <!-- Persons -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('persons',
                                                        concat(col[@field='First Name'], '/',
                                                               col[@field='Last Name'], '/',
                                                               col[@field='Email']))[1])]">
                <xsl:call-template name="Person"/>
            </xsl:for-each>

            <!-- Process all table rows for person records -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Event">

        <xsl:variable name="SiteName" select="col[@field='Facility']/text()"/>
        <xsl:variable name="CourseName" select="col[@field='Course']/text()"/>
        <xsl:variable name="Start" select="col[@field='Start']/text()"/>

        <resource name="hrm_training_event">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($SiteName, '/',
                                             $CourseName, '/',
                                             $Start)"/>
            </xsl:attribute>
            <data field="start_date"><xsl:value-of select="$Start"/></data>
            <data field="end_date"><xsl:value-of select="col[@field='End']/text()"/></data>
            <data field="hours"><xsl:value-of select="col[@field='Hours']/text()"/></data>
            <!-- Link to Course -->
            <reference field="course_id" resource="hrm_course">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$CourseName"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Site -->
            <reference field="site_id" resource="org_office">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$SiteName"/>
                </xsl:attribute>
            </reference>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Person Record -->
    <xsl:template name="Person">

        <xsl:variable name="gender">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$PersonGender"/>
            </xsl:call-template>
        </xsl:variable>

        <resource name="pr_person">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat(col[@field='First Name'], '/',
                                             col[@field='Last Name'], '/',
                                             col[@field='Email'])"/>
            </xsl:attribute>
            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
            <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
            <xsl:if test="$gender!=''">
                <data field="gender">
                    <xsl:attribute name="value"><xsl:value-of select="$gender"/></xsl:attribute>
                </data>
            </xsl:if>
            <xsl:call-template name="ContactInformation"/>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="SiteName" select="col[@field='Facility']/text()"/>
        <xsl:variable name="CourseName" select="col[@field='Course']/text()"/>
        <xsl:variable name="Start" select="col[@field='Start']/text()"/>

        <resource name="hrm_training">
            <reference field="training_event_id" resource="hrm_training_event">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($SiteName, '/',
                                                 $CourseName, '/',
                                                 $Start)"/>
                </xsl:attribute>
            </reference>
            <reference field="person_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat(col[@field='First Name'], '/',
                                                 col[@field='Last Name'], '/',
                                                 col[@field='Email'])"/>
                </xsl:attribute>
            </reference>
            <reference field="course_id" resource="hrm_course">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Course']"/>
                </xsl:attribute>
            </reference>
            <data field="date"><xsl:value-of select="col[@field='Start']"/></data>
            <data field="hours"><xsl:value-of select="col[@field='Hours']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Course">
        <xsl:variable name="CourseName" select="col[@field='Course']/text()"/>

        <resource name="hrm_course">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$CourseName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$CourseName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Defined in person.xsl
    <xsl:template name="Organisation">
        <xsl:variable name="OrganisationName" select="col[@field='Organisation']/text()"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OrganisationName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrganisationName"/></data>
        </resource>

    </xsl:template> -->

    <!-- ****************************************************************** -->
    <xsl:template name="Site">
        <xsl:variable name="SiteName" select="col[@field='Facility']/text()"/>
        <xsl:variable name="OrganisationName" select="col[@field='Organisation']/text()"/>

        <resource name="org_office">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$SiteName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$SiteName"/></data>
            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OrganisationName"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
