<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:hrm="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Training Participant List - CSV Import Stylesheet

         Column headers defined in this stylesheet:
         Training Event (just used for setting defaults) @ToDo: Complete this
         Course
         Organisation
         Facility
         Start
         End
         Hours
         First Name
         Middle Name
         Last Name
         Sex
         Email
         DoB
         National ID

         Column headers looked up in labels.xml:

         PersonGender...................optional.....person gender

         @ToDo: Support Facilities other than Offices

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="./person.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Index for faster processing & deduplication -->
    <xsl:key name="courses" match="row" use="col[@field='Course']"/>
    <xsl:key name="organisations" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="sites" match="row" use="col[@field='Facility']"/>
    <xsl:key name="persons" match="row" use="concat(col[@field='First Name'], '/',
                                                    col[@field='Middle Name'], '/',
                                                    col[@field='Last Name'], '/',
                                                    col[@field='DoB'], '/',
                                                    col[@field='National ID'], '/',
                                                    col[@field='Email'])"/>
    <xsl:key name="events" match="row" use="concat(col[@field='Facility'], '/',
                                                   col[@field='Course'], '/',
                                                   col[@field='Start'])"/>
    <xsl:key name="trainingevents" match="row" use="col[@field='Training Event']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Training Events -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('trainingevents',
                                                                   col[@field='Training Event'])[1])]">
                <xsl:call-template name="TrainingEvent"/>
            </xsl:for-each>

            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisations',
                                                                   col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName">
                        <xsl:value-of select="col[@field='Organisation']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
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
                                                               col[@field='Middle Name'], '/',
                                                               col[@field='Last Name'], '/',
                                                               col[@field='DoB'], '/',
                                                               col[@field='National ID'], '/',
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
        <xsl:variable name="StartDate" select="col[@field='Start']/text()"/>

        <xsl:if test="$SiteName!=''">
            <resource name="hrm_training_event">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($SiteName, '/',
                                                 $CourseName, '/',
                                                 $StartDate)"/>
                </xsl:attribute>
                <data field="start_date"><xsl:value-of select="$StartDate"/></data>
                <data field="end_date"><xsl:value-of select="col[@field='End']"/></data>
                <data field="hours"><xsl:value-of select="col[@field='Hours']"/></data>
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
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="TrainingEvent">
        <xsl:variable name="TrainingEvent" select="col[@field='Training Event']/text()"/>

        <xsl:if test="$TrainingEvent!=''">
            <!-- Training Event represent has been provided by csv_extra_fields, this needs to be decomposed -->
            <xsl:variable name="CourseName">
                <xsl:value-of select="substring-before($TrainingEvent, ' --')"/>
            </xsl:variable>
            <xsl:variable name="tail">
                <xsl:value-of select="substring-after($TrainingEvent, '--')"/>
            </xsl:variable>
            <xsl:variable name="OfficeName">
                <!-- enclosed in curly brackets -->
                <xsl:value-of select="substring-before(substring-after($tail, '{'), '}')"/>
            </xsl:variable>
            <xsl:variable name="StartDate">
                <!-- enclosed in square brackets -->
                <xsl:value-of select="substring-before(substring-after($tail, '['), ']')"/>
            </xsl:variable>

            <xsl:if test="$CourseName!=''">
                <resource name="hrm_course">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$CourseName"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$CourseName"/></data>
                </resource>
                <xsl:if test="$OfficeName!=''">
                    <resource name="org_office">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OfficeName"/>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="$OfficeName"/></data>
                    </resource>
                </xsl:if>
                <resource name="hrm_training_event">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('TrainingEvent/', $TrainingEvent)"/>
                    </xsl:attribute>
                    <data field="start_date"><xsl:value-of select="$StartDate"/></data>
                    <!-- Link to Course -->
                    <reference field="course_id" resource="hrm_course">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$CourseName"/>
                        </xsl:attribute>
                    </reference>
                    <!-- Link to Site -->
                    <xsl:if test="$OfficeName!=''">
                        <reference field="site_id" resource="org_office">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$OfficeName"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:if>
                </resource>
            </xsl:if>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Person Record -->
    <xsl:template name="Person">
        <xsl:variable name="FirstName" select="col[@field='First Name']/text()"/>
        <xsl:variable name="MiddleName" select="col[@field='Middle Name']/text()"/>
        <xsl:variable name="LastName" select="col[@field='Last Name']/text()"/>
        <xsl:variable name="DoB" select="col[@field='DoB']/text()"/>
        <xsl:variable name="NationalID" select="col[@field='National ID']/text()"/>

        <xsl:variable name="gender">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$PersonGender"/>
            </xsl:call-template>
        </xsl:variable>

        <resource name="pr_person">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($FirstName, '/',
                                             $MiddleName, '/',
                                             $LastName, '/',
                                             $DoB, '/',
                                             $NationalID, '/',
                                             col[@field='Email'])"/>
            </xsl:attribute>
            <data field="first_name"><xsl:value-of select="$FirstName"/></data>
            <xsl:if test="$MiddleName!=''">
                <data field="middle_name"><xsl:value-of select="$MiddleName"/></data>
            </xsl:if>
            <xsl:if test="$LastName!=''">
                <data field="last_name"><xsl:value-of select="$LastName"/></data>
            </xsl:if>
            <xsl:if test="$DoB!=''">
                <data field="date_of_birth"><xsl:value-of select="$DoB"/></data>
            </xsl:if>
            <xsl:if test="$gender!=''">
                <data field="gender">
                    <xsl:attribute name="value"><xsl:value-of select="$gender"/></xsl:attribute>
                </data>
            </xsl:if>
            <xsl:if test="$NationalID!=''">
                <resource name="pr_identity">
                    <data field="type" value="2"/>
                    <data field="value"><xsl:value-of select="$NationalID"/></data>
                </resource>
            </xsl:if>
            <xsl:call-template name="ContactInformation"/>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="SiteName" select="col[@field='Facility']/text()"/>
        <xsl:variable name="StartDate" select="col[@field='Start']/text()"/>
        <xsl:variable name="EndDate" select="col[@field='End']/text()"/>
        <xsl:variable name="Hours" select="col[@field='Hours']/text()"/>
        <xsl:variable name="TrainingEvent" select="col[@field='Training Event']/text()"/>
        <xsl:variable name="CourseName">
            <xsl:choose>
                <xsl:when test="$TrainingEvent!=''">
                    <xsl:value-of select="substring-before($TrainingEvent, ' --')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="col[@field='Course']/text()"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <resource name="hrm_training">
            <xsl:choose>
                <xsl:when test="$TrainingEvent!=''">
                    <reference field="training_event_id" resource="hrm_training_event">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('TrainingEvent/', $TrainingEvent)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$SiteName!=''">
                    <reference field="training_event_id" resource="hrm_training_event">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($SiteName, '/',
                                                         $CourseName, '/',
                                                         $StartDate)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
            </xsl:choose>
            <reference field="person_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat(col[@field='First Name'], '/',
                                                 col[@field='Middle Name'], '/',
                                                 col[@field='Last Name'], '/',
                                                 col[@field='DoB'], '/',
                                                 col[@field='National ID'], '/',
                                                 col[@field='Email'])"/>
                </xsl:attribute>
            </reference>
            <xsl:if test="$CourseName!=''">
                <reference field="course_id" resource="hrm_course">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$CourseName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="$StartDate!=''">
                <data field="date"><xsl:value-of select="$StartDate"/></data>
            </xsl:if>
            <xsl:if test="$EndDate!=''">
                <data field="end_date"><xsl:value-of select="$EndDate"/></data>
            </xsl:if>
            <xsl:if test="$Hours!=''">
                <data field="hours"><xsl:value-of select="$Hours"/></data>
            </xsl:if>
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

        <resource name="org_office">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$SiteName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$SiteName"/></data>
            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Organisation']"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
