<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:hrm="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Training Participant List - CSV Import Stylesheet

         Column headers defined in this stylesheet:
         Training Event (just used for setting defaults) @ToDo: Complete this
         Training Organisation
         Course
         Venue
         Venue Type
         Start
         End
         Hours
         Grade
         Trainee Organisation
         HR Type
         Certificate Number
         First Name
         Middle Name (Apellido Paterno in Spanish)
         Last Name   (Apellido Materno in Spanish)
         Sex
         Email
         DoB
         National ID

         If wanting to create Users:
         #Password
         Language

         Column headers looked up in labels.xml:

         PersonGender...................optional.....person gender
         MiddleName.....................optional.....person Middle Name (Apellido Paterno in Spanish)
         LastName.......................optional.....person Last Name   (Apellido Materno in Spanish)

    *********************************************************************** -->
    <xsl:import href="person.xsl"/>
    <xsl:import href="../commons.xsl"/>

    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Index for faster processing & deduplication -->
    <xsl:key name="courses" match="row" use="col[@field='Course']"/>
    <xsl:key name="organisations" match="row" use="col[@field='Trainee Organisation']"/>
    <xsl:key name="organisers" match="row" use="col[@field='Training Organisation']"/>
    <xsl:key name="sites" match="row" use="concat(col[@field='Venue'], '/',
                                                  col[@field='Facility Type'])"/>
    <xsl:key name="persons" match="row" use="concat(col[@field='First Name'], '/',
                                                    col[@field='Middle Name'], '/',
                                                    col[@field='Last Name'], '/',
                                                    col[@field='DoB'], '/',
                                                    col[@field='National ID'], '/',
                                                    col[@field='Email'])"/>
    <xsl:key name="events" match="row" use="concat(col[@field='Venue'], '/',
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
                                                                   col[@field='Trainee Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="Field">Trainee Organisation</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisers',
                                                                   col[@field='Training Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="Field">Training Organisation</xsl:with-param>
                </xsl:call-template>
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
                <xsl:call-template name="Certificate"/>
            </xsl:for-each>

            <!-- Events -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('events',
                                                        concat(col[@field='Venue'], '/',
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
        <xsl:variable name="Organisation" select="col[@field='Training Organisation']/text()"/>
        <xsl:variable name="SiteName" select="col[@field='Venue']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>
        <xsl:variable name="CourseName" select="col[@field='Course']/text()"/>
        <xsl:variable name="StartDate" select="col[@field='Start']/text()"/>
        <xsl:variable name="Hours" select="col[@field='Hours']/text()"/>

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

        <xsl:if test="$SiteName!=''">
            <resource name="hrm_training_event">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($SiteName, '/',
                                                 $CourseName, '/',
                                                 $StartDate)"/>
                </xsl:attribute>
                <data field="start_date"><xsl:value-of select="$StartDate"/></data>
                <data field="end_date"><xsl:value-of select="col[@field='End']"/></data>
                <xsl:if test="$Hours!=''">
                    <data field="hours"><xsl:value-of select="$Hours"/></data>
                </xsl:if>
                <!-- Link to Organisation -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Organisation"/>
                    </xsl:attribute>
                </reference>
                <!-- Link to Course -->
                <reference field="course_id" resource="hrm_course">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$CourseName"/>
                    </xsl:attribute>
                </reference>
                <!-- Link to Site -->
                <reference field="site_id">
                    <xsl:attribute name="resource">
                        <xsl:value-of select="$resourcename"/>
                    </xsl:attribute>
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
            <xsl:variable name="SiteName">
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
                <xsl:if test="$SiteName!=''">
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
        <xsl:variable name="DoB" select="col[@field='DoB']/text()"/>
        <xsl:variable name="NationalID" select="col[@field='National ID']/text()"/>
        <xsl:variable name="Email" select="col[@field='Email']/text()"/>
        <xsl:variable name="Organisation" select="col[@field='Trainee Organisation']/text()"/>
        <xsl:variable name="HRType">
            <xsl:call-template name="lowercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='HR Type']/text()"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <!--<xsl:variable name="Password" select="col[@field='Password']/text()"/>-->
        <xsl:variable name="Language" select="col[@field='Language']/text()"/>
        <xsl:variable name="Certification" select="col[@field='Certificate Number']/text()"/>

        <xsl:variable name="MiddleName">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$MiddleName"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="LastName">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$LastName"/>
            </xsl:call-template>
        </xsl:variable>
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
                                             $Email)"/>
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
            <xsl:if test="$Language!=''">
                <resource name="pr_person_details">
                    <data field="language"><xsl:value-of select="$Language"/></data>
                </resource>
            </xsl:if>

            <!-- Email -->
            <xsl:call-template name="ContactInformation"/>

            <xsl:if test="$Organisation!=''">
                <!-- HR record -->
                <resource name="hrm_human_resource">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$Organisation"/>
                        </xsl:attribute>
                    </reference>
                    <xsl:if test="$HRType!=''">
                        <xsl:choose>
                            <xsl:when test="$HRType='volunteer'">
                                <data field="type" value="2"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <!-- Default to Staff -->
                                <data field="type" value="1"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:if>
                </resource>
            </xsl:if>

            <!-- Can't reliably link to persons as these are imported in random order
                 - do this postimport if desired (see RMSAmericas)
            <xsl:if test="$Password!=''">
                <!- - User Account
                <resource name="pr_person_user">
                    <reference field="user_id" resource="auth_user">
                        <resource name="auth_user">
                            <data field="first_name"><xsl:value-of select="$FirstName"/></data>
                            <xsl:choose>
                                <xsl:when test="$LastName!=''">
                                    <data field="last_name"><xsl:value-of select="$LastName"/></data>
                                </xsl:when>
                                <xsl:when test="$MiddleName!=''">
                                    <!- - e.g. Apellido Paterno
                                    <data field="last_name"><xsl:value-of select="$MiddleName"/></data>
                                </xsl:when>
                            </xsl:choose>
                            <data field="email"><xsl:value-of select="$Email"/></data>
                            <!- - This will overwrite password for existing users :/
                            <data field="password">
                                <xsl:attribute name="value">
                                    <xsl:value-of select="$Password"/>
                                </xsl:attribute>
                            </data>
                            <xsl:if test="col[@field='Language']!=''">
                                <data field="language"><xsl:value-of select="col[@field='Language']"/></data>
                            </xsl:if>
                            <xsl:if test="$HRType!=''">
                                <data field="link_user_to"><xsl:value-of select="$HRType"/></data>
                            </xsl:if>

                            <!- - Link to Organisation
                            <xsl:if test="$Organisation!=''">
                                <reference field="organisation_id" resource="org_organisation">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="$Organisation"/>
                                    </xsl:attribute>
                                </reference>
                            </xsl:if>
                        </resource>
                    </reference>
                </resource>
            </xsl:if>-->

            <!-- @ToDo: Allow multiple Certifications for the same person! -->
            <xsl:if test="$Certification!=''">
                <!-- Certification -->
                <resource name="hrm_certification">
                    <reference field="certificate_id" resource="hrm_certificate">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='Course']"/>
                        </xsl:attribute>
                    </reference>
                    <data field="number"><xsl:value-of select="$Certification"/></data>
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='Training Organisation']"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="SiteName" select="col[@field='Venue']/text()"/>
        <xsl:variable name="StartDate" select="col[@field='Start']/text()"/>
        <xsl:variable name="EndDate" select="col[@field='End']/text()"/>
        <xsl:variable name="Hours" select="col[@field='Hours']/text()"/>
        <xsl:variable name="Grade" select="col[@field='Grade']/text()"/>
        <xsl:variable name="GradeDetails">
            <xsl:value-of select="substring-after($Grade, '.')"/>
        </xsl:variable>
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
            <xsl:choose>
                <xsl:when test="$GradeDetails!=''">
                    <!-- Fractional Data, so this is a specific test result -->
                    <data field="grade_details">
                        <xsl:value-of select="$Grade"/>
                    </data>
                </xsl:when>
                <xsl:when test="$Grade!=''">
                    <data field="grade">
                        <xsl:choose>
                            <xsl:when test="$Grade='Pass'">8</xsl:when>
                            <xsl:when test="$Grade='Aprobado'">8</xsl:when>
                            <xsl:when test="$Grade='Fail'">9</xsl:when>
                            <xsl:when test="$Grade='Reprobado'">9</xsl:when>
                            <xsl:otherwise><xsl:value-of select="$Grade"/></xsl:otherwise>
                        </xsl:choose>
                    </data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Assume a Pass -->
                    <data field="grade">8</data>
                </xsl:otherwise>
            </xsl:choose>
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
    <xsl:template name="Certificate">
        <!-- @ToDo: Add Support for Certs with diff names to Courses -->
        <xsl:variable name="CourseName" select="col[@field='Course']/text()"/>

        <xsl:if test="col[@field='Certificate Number']!=''">
            <resource name="hrm_certificate">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$CourseName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$CourseName"/></data>
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='Training Organisation']"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Site">
        <xsl:variable name="SiteName" select="col[@field='Venue']/text()"/>
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
            <!-- Link to Organisation. No: Leave this to deduplicator
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Organisation']"/>
                </xsl:attribute>
            </reference> -->
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
