<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:hrm="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Training Participant List - CSV Import Stylesheet

         Column headers defined in this stylesheet:
         Training Event (just used for setting defaults) @ToDo: Complete this
         Training Organisation
         Event Name
         Event Type
         Strategy
         Programme
         Project
         Course

         Venue
         Venue Type
            OR
         Training L0
         Training L1
         Training L2
         Training L3
         Training L4
         Training L5

         Start
         End
         Hours
         Role
         Grade
         Qualitative Feedback
         Trainee Organisation
         HR Type
         Department
         Office L0
         Office L1
         Office L2
         Office L3
         Office L4
         Office L5
         Job Title
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
    <!-- Lookup column names -->

    <xsl:variable name="PersonGender">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">PersonGender</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="MiddleName">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">MiddleName</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="LastName">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">LastName</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="JobTitle">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">JobTitle</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Index for faster processing & deduplication -->
    <xsl:key name="courses" match="row" use="col[@field='Course']"/>
    <xsl:key name="event_types" match="row" use="col[@field='Event Type']"/>
    <xsl:key name="strategies" match="row" use="col[@field='Strategy']"/>
    <xsl:key name="programmes" match="row" use="col[@field='Programme']"/>
    <xsl:key name="projects" match="row" use="col[@field='Project']"/>
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
    <xsl:key name="events" match="row" use="concat(col[@field='Training L0'], '/',
                                                   col[@field='Training L1'], '/',
                                                   col[@field='Training L2'], '/',
                                                   col[@field='Training L3'], '/',
                                                   col[@field='Venue'], '/',
                                                   col[@field='Course'], '/',
                                                   col[@field='Start'])"/>
    <xsl:key name="trainingevents" match="row" use="col[@field='Training Event']"/>

    <xsl:key name="departments" match="row"
             use="concat(col[@field='Trainee Organisation'], '/', col[@field='Department'])"/>
    <xsl:key name="jobtitles" match="row"
             use="concat(col[@field='Trainee Organisation'], '/',
                         col[contains(
                             document('../labels.xml')/labels/column[@name='JobTitle']/match/text(),
                             concat('|', @field, '|'))])"/>

    <xsl:key name="OL1" match="row"
             use="concat(col[@field='Office L0'], '/',
                         col[@field='Office L1'])"/>
    <xsl:key name="OL2" match="row"
             use="concat(col[@field='Office L0'], '/',
                         col[@field='Office L1'], '/',
                         col[@field='Office L2'])"/>
    <xsl:key name="OL3" match="row"
             use="concat(col[@field='Office L0'], '/',
                         col[@field='Office L1'], '/',
                         col[@field='Office L2'], '/',
                         col[@field='Office L3'])"/>
    <xsl:key name="OL4" match="row"
             use="concat(col[@field='Office L0'], '/',
                         col[@field='Office L1'], '/',
                         col[@field='Office L2'], '/',
                         col[@field='Office L3'], '/',
                         col[@field='Office L4'])"/>
    <xsl:key name="OL5" match="row"
             use="concat(col[@field='Office L0'], '/',
                         col[@field='Office L1'], '/',
                         col[@field='Office L2'], '/',
                         col[@field='Office L3'], '/',
                         col[@field='Office L4'], '/',
                         col[@field='Office L5'])"/>
    <xsl:key name="offices" match="row"
             use="concat(col[@field='Trainee Organisation'], '/',
                         col[@field='Office L0'], '/',
                         col[@field='Office L1'], '/',
                         col[@field='Office L2'], '/',
                         col[@field='Office L3'], '/',
                         col[@field='Office L4'], '/',
                         col[@field='Office L5'])"/>

    <xsl:key name="TL1" match="row"
             use="concat(col[@field='Training L0'], '/',
                         col[@field='Training L1'])"/>
    <xsl:key name="TL2" match="row"
             use="concat(col[@field='Training L0'], '/',
                         col[@field='Training L1'], '/',
                         col[@field='Training L2'])"/>
    <xsl:key name="TL3" match="row"
             use="concat(col[@field='Training L0'], '/',
                         col[@field='Training L1'], '/',
                         col[@field='Training L2'], '/',
                         col[@field='Training L3'])"/>
    <xsl:key name="TL4" match="row"
             use="concat(col[@field='Training L0'], '/',
                         col[@field='Training L1'], '/',
                         col[@field='Training L2'], '/',
                         col[@field='Training L3'], '/',
                         col[@field='Training L4'])"/>

    <xsl:key name="TL5" match="row"
             use="concat(col[@field='Training L0'], '/',
                         col[@field='Training L1'], '/',
                         col[@field='Training L2'], '/',
                         col[@field='Training L3'], '/',
                         col[@field='Training L4'], '/',
                         col[@field='Training L5'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- L1 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('OL1',
                                                                   concat(col[@field='Office L0'], '/',
                                                                          col[@field='Office L1']))[1])]">
                <xsl:call-template name="L1">
                    <xsl:with-param name="L0">
                        <xsl:value-of select="col[@field='Office L0']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L1">
                        <xsl:value-of select="col[@field='Office L1']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('TL1',
                                                                   concat(col[@field='Training L0'], '/',
                                                                          col[@field='Training L1']))[1])]">
                <xsl:call-template name="L1">
                    <xsl:with-param name="L0">
                        <xsl:value-of select="col[@field='Training L0']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L1">
                        <xsl:value-of select="col[@field='Training L1']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- L2 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('OL2',
                                                                   concat(col[@field='Office L0'], '/',
                                                                          col[@field='Office L1'], '/',
                                                                          col[@field='Office L2']))[1])]">
                <xsl:call-template name="L2">
                    <xsl:with-param name="L0">
                        <xsl:value-of select="col[@field='Office L0']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L1">
                        <xsl:value-of select="col[@field='Office L1']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L2">
                        <xsl:value-of select="col[@field='Office L2']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('TL2',
                                                                   concat(col[@field='Training L0'], '/',
                                                                          col[@field='Training L1'], '/',
                                                                          col[@field='Training L2']))[1])]">
                <xsl:call-template name="L2">
                    <xsl:with-param name="L0">
                        <xsl:value-of select="col[@field='Training L0']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L1">
                        <xsl:value-of select="col[@field='Training L1']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L2">
                        <xsl:value-of select="col[@field='Training L2']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- L3 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('OL3',
                                                                   concat(col[@field='Office L0'], '/',
                                                                          col[@field='Office L1'], '/',
                                                                          col[@field='Office L2'], '/',
                                                                          col[@field='Office L3']))[1])]">
                <xsl:call-template name="L3">
                    <xsl:with-param name="L0">
                        <xsl:value-of select="col[@field='Office L0']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L1">
                        <xsl:value-of select="col[@field='Office L1']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L2">
                        <xsl:value-of select="col[@field='Office L2']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L3">
                        <xsl:value-of select="col[@field='Office L3']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('TL3',
                                                                   concat(col[@field='Training L0'], '/',
                                                                          col[@field='Training L1'], '/',
                                                                          col[@field='Training L2'], '/',
                                                                          col[@field='Training L3']))[1])]">
                <xsl:call-template name="L3">
                    <xsl:with-param name="L0">
                        <xsl:value-of select="col[@field='Training L0']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L1">
                        <xsl:value-of select="col[@field='Training L1']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L2">
                        <xsl:value-of select="col[@field='Training L2']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L3">
                        <xsl:value-of select="col[@field='Training L3']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- L4 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('OL4',
                                                                   concat(col[@field='Office L0'], '/',
                                                                          col[@field='Office L1'], '/',
                                                                          col[@field='Office L2'], '/',
                                                                          col[@field='Office L3'], '/',
                                                                          col[@field='Office L4']))[1])]">
                <xsl:call-template name="L4">
                    <xsl:with-param name="L0">
                        <xsl:value-of select="col[@field='Office L0']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L1">
                        <xsl:value-of select="col[@field='Office L1']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L2">
                        <xsl:value-of select="col[@field='Office L2']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L3">
                        <xsl:value-of select="col[@field='Office L3']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L4">
                        <xsl:value-of select="col[@field='Office L4']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('TL4',
                                                                   concat(col[@field='Training L0'], '/',
                                                                          col[@field='Training L1'], '/',
                                                                          col[@field='Training L2'], '/',
                                                                          col[@field='Training L3'], '/',
                                                                          col[@field='Training L4']))[1])]">
                <xsl:call-template name="L4">
                    <xsl:with-param name="L0">
                        <xsl:value-of select="col[@field='Training L0']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L1">
                        <xsl:value-of select="col[@field='Training L1']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L2">
                        <xsl:value-of select="col[@field='Training L2']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L3">
                        <xsl:value-of select="col[@field='Training L3']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L4">
                        <xsl:value-of select="col[@field='Training L4']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>


            <!-- L5 -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('OL5',
                                                                   concat(col[@field='Office L0'], '/',
                                                                          col[@field='Office L1'], '/',
                                                                          col[@field='Office L2'], '/',
                                                                          col[@field='Office L3'], '/',
                                                                          col[@field='Office L4'], '/',
                                                                          col[@field='Office L5']))[1])]">
                <xsl:call-template name="L5">
                    <xsl:with-param name="L0">
                        <xsl:value-of select="col[@field='Office L0']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L1">
                        <xsl:value-of select="col[@field='Office L1']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L2">
                        <xsl:value-of select="col[@field='Office L2']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L3">
                        <xsl:value-of select="col[@field='Office L3']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L4">
                        <xsl:value-of select="col[@field='Office L4']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L5">
                        <xsl:value-of select="col[@field='Office L5']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('TL5',
                                                                   concat(col[@field='Training L0'], '/',
                                                                          col[@field='Training L1'], '/',
                                                                          col[@field='Training L2'], '/',
                                                                          col[@field='Training L3'], '/',
                                                                          col[@field='Training L4'], '/',
                                                                          col[@field='Training L5']))[1])]">
                <xsl:call-template name="L5">
                    <xsl:with-param name="L0">
                        <xsl:value-of select="col[@field='Training L0']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L1">
                        <xsl:value-of select="col[@field='Training L1']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L2">
                        <xsl:value-of select="col[@field='Training L2']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L3">
                        <xsl:value-of select="col[@field='Training L3']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L4">
                        <xsl:value-of select="col[@field='Training L4']"/>
                    </xsl:with-param>
                    <xsl:with-param name="L5">
                        <xsl:value-of select="col[@field='Training L5']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

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

            <!-- Event Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('event_types',
                                                                   col[@field='Event Type'])[1])]">
                <xsl:call-template name="EventType"/>
            </xsl:for-each>

            <!-- Strategies -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('strategies',
                                                                   col[@field='Strategy'])[1])]">
                <xsl:call-template name="Strategy"/>
            </xsl:for-each>

            <!-- Programmes -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('programmes',
                                                                   col[@field='Programme'])[1])]">
                <xsl:call-template name="Programme"/>
            </xsl:for-each>

            <!-- Projects -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('projects',
                                                                   col[@field='Project'])[1])]">
                <xsl:call-template name="Project"/>
            </xsl:for-each>

            <!-- Events -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('events',
                                                        concat(col[@field='Training L0'], '/',
                                                               col[@field='Training L1'], '/',
                                                               col[@field='Training L2'], '/',
                                                               col[@field='Training L3'], '/',
                                                               col[@field='Venue'], '/',
                                                               col[@field='Course'], '/',
                                                               col[@field='Start']))[1])]">
                <xsl:call-template name="Event"/>
            </xsl:for-each>

            <!-- Departments -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('departments',
                                                        concat(col[@field='Trainee Organisation'], '/',
                                                               col[@field='Department']))[1])]">
                <xsl:call-template name="Department">
                    <xsl:with-param name="type">resource</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Offices -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('offices',
                                                        concat(col[@field='Trainee Organisation'], '/',
                                                               col[@field='Office L0'], '/',
                                                               col[@field='Office L1'], '/',
                                                               col[@field='Office L2'], '/',
                                                               col[@field='Office L3'], '/',
                                                               col[@field='Office L4'], '/',
                                                               col[@field='Office L5']))[1])]">
                <xsl:call-template name="Office">
                    <xsl:with-param name="type">resource</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Job Titles -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('jobtitles',
                                            concat(col[@field='Trainee Organisation'], '/',
                                                   col[contains(
                                                       document('../labels.xml')/labels/column[@name='JobTitle']/match/text(),
                                                       concat('|', @field, '|'))])
                                        )[1])]">
                <xsl:call-template name="JobTitle">
                    <xsl:with-param name="type">resource</xsl:with-param>
                </xsl:call-template>
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
        <xsl:variable name="SiteName" select="col[@field='Venue']/text()"/>
        <xsl:variable name="L0" select="col[@field='Training L0']/text()"/>

        <xsl:if test="$SiteName!='' or $L0!=''">
            <xsl:variable name="Organisation" select="col[@field='Training Organisation']/text()"/>
            <xsl:variable name="EventType" select="col[@field='Event Type']/text()"/>
            <xsl:variable name="Strategy" select="col[@field='Strategy']/text()"/>
            <xsl:variable name="Programme" select="col[@field='Programme']/text()"/>
            <xsl:variable name="Project" select="col[@field='Project']/text()"/>
            <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>
            <xsl:variable name="CourseName" select="col[@field='Course']/text()"/>
            <xsl:variable name="StartDate" select="col[@field='Start']/text()"/>
            <xsl:variable name="Hours" select="col[@field='Hours']/text()"/>
            <xsl:variable name="L1" select="col[@field='Training L1']/text()"/>
            <xsl:variable name="L2" select="col[@field='Training L2']/text()"/>
            <xsl:variable name="L3" select="col[@field='Training L3']/text()"/>

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

            <resource name="hrm_training_event">
                 <xsl:choose>
                    <xsl:when test="$SiteName!=''">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($SiteName, '/',
                                                         $CourseName, '/',
                                                         $StartDate)"/>
                        </xsl:attribute>
                    </xsl:when>
                    <xsl:when test="$L0!=''">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($L0, '/',
                                                         $L1, '/',
                                                         $L2, '/',
                                                         $L3, '/',
                                                         $CourseName, '/',
                                                         $StartDate)"/>
                        </xsl:attribute>
                    </xsl:when>
                </xsl:choose>
                <data field="name"><xsl:value-of select="col[@field='Event Name']"/></data>
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
                <xsl:if test="$EventType!=''">
                    <!-- Link to Event Type -->
                    <reference field="event_type_id" resource="hrm_event_type">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$EventType"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
                <xsl:if test="$Strategy!=''">
                    <!-- Link to Strategy -->
                    <resource name="hrm_event_strategy">
                        <reference field="strategy_id" resource="project_strategy">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$Strategy"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>
                <xsl:if test="$Programme!=''">
                    <!-- Link to Programme -->
                    <resource name="hrm_programme_event">
                        <reference field="programme_id" resource="hrm_programme">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$Programme"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>
                <xsl:if test="$Project!=''">
                    <!-- Link to Project -->
                    <resource name="hrm_event_project">
                        <reference field="project_id" resource="project_project">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$Project"/>
                            </xsl:attribute>
                        </reference>
                    </resource>
                </xsl:if>
                <xsl:if test="$CourseName!=''">
                    <!-- Link to Course -->
                    <reference field="course_id" resource="hrm_course">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$CourseName"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
                <xsl:if test="$SiteName!=''">
                    <!-- Link to Site -->
                    <reference field="site_id">
                        <xsl:attribute name="resource">
                            <xsl:value-of select="$resourcename"/>
                        </xsl:attribute>
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$SiteName"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
                <xsl:if test="$L0!=''">
                    <!-- Link to Location -->
                    <xsl:variable name="L4" select="col[@field='Training L4']/text()"/>
                    <xsl:variable name="L5" select="col[@field='Training L5']/text()"/>

                    <!-- Country Code = UUID of the L0 Location -->
                    <xsl:variable name="countrycode">
                        <xsl:choose>
                            <xsl:when test="string-length($L0)!=2">
                                <xsl:call-template name="countryname2iso">
                                    <xsl:with-param name="country">
                                        <xsl:value-of select="$L0"/>
                                    </xsl:with-param>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$L0"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>

                    <reference field="location_id" resource="gis_location">
                        <xsl:choose>
                            <xsl:when test="$L5!=''">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="concat('L5/', $countrycode, '/', $L1, '/', $L2, '/', $L3, '/', $L4, '/', $L5)"/>
                                </xsl:attribute>
                            </xsl:when>
                            <xsl:when test="$L4!=''">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="concat('L4/', $countrycode, '/', $L1, '/', $L2, '/', $L3, '/', $L4)"/>
                                </xsl:attribute>
                            </xsl:when>
                            <xsl:when test="$L3!=''">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="concat('L3/', $countrycode, '/', $L1, '/', $L2, '/', $L3)"/>
                                </xsl:attribute>
                            </xsl:when>
                            <xsl:when test="$L2!=''">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="concat('L2/', $countrycode, '/', $L1, '/', $L2)"/>
                                </xsl:attribute>
                            </xsl:when>
                            <xsl:when test="$L1!=''">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="concat('L1/', $countrycode, '/', $L1)"/>
                                </xsl:attribute>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:variable name="country"
                                              select="concat('urn:iso:std:iso:3166:-1:code:',
                                                             $countrycode)"/>
                                <xsl:attribute name="uuid">
                                    <xsl:value-of select="$country"/>
                                </xsl:attribute>
                            </xsl:otherwise>
                        </xsl:choose>
                    </reference>
                </xsl:if>

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

                    <!-- Link to Department -->
                    <xsl:call-template name="Department">
                        <xsl:with-param name="type">reference</xsl:with-param>
                    </xsl:call-template>

                    <!-- Link to Office -->
                    <xsl:call-template name="Office">
                        <xsl:with-param name="type">reference</xsl:with-param>
                    </xsl:call-template>

                    <!-- Link to Job Title -->
                    <xsl:call-template name="JobTitle">
                        <xsl:with-param name="type">reference</xsl:with-param>
                    </xsl:call-template>
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

        <xsl:variable name="L0" select="col[@field='Training L0']/text()"/>
        <xsl:variable name="SiteName" select="col[@field='Venue']/text()"/>
        <xsl:variable name="StartDate" select="col[@field='Start']/text()"/>
        <xsl:variable name="EndDate" select="col[@field='End']/text()"/>
        <xsl:variable name="Hours" select="col[@field='Hours']/text()"/>
        <xsl:variable name="Role" select="col[@field='Role']/text()"/>
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
                <xsl:when test="$L0!=''">
                    <xsl:variable name="L1" select="col[@field='Training L1']/text()"/>
                    <xsl:variable name="L2" select="col[@field='Training L2']/text()"/>
                    <xsl:variable name="L3" select="col[@field='Training L3']/text()"/>
                    <reference field="training_event_id" resource="hrm_training_event">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($L0, '/',
                                                         $L1, '/',
                                                         $L2, '/',
                                                         $L3, '/',
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
            <xsl:if test="$Role!=''">
                <data field="role">
                    <xsl:choose>
                        <xsl:when test="$Role='Participant'">1</xsl:when>
                        <xsl:when test="$Role='Facilitator'">2</xsl:when>
                        <xsl:when test="$Role='Observer'">3</xsl:when>
                        <xsl:otherwise>1</xsl:otherwise>
                    </xsl:choose>
                </data>
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
            <data field="qualitative_feedback">
                <xsl:value-of select="col[@field='Qualitative Feedback']"/>
            </data>
        </resource>

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
    <xsl:template name="EventType">
        <xsl:variable name="Name" select="col[@field='Event Type']/text()"/>

        <xsl:if test="$Name!=''">
            <resource name="hrm_event_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Name"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Name"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Strategy">
        <xsl:variable name="Name" select="col[@field='Strategy']/text()"/>

        <xsl:if test="$Name!=''">
            <resource name="project_strategy">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Name"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Name"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Programme">
        <xsl:variable name="Name" select="col[@field='Programme']/text()"/>

        <xsl:if test="$Name!=''">
            <resource name="hrm_programme">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Name"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Name"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Project">
        <xsl:variable name="Name" select="col[@field='Project']/text()"/>

        <xsl:if test="$Name!=''">
            <resource name="project_project">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$Name"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Name"/></data>
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
                <!-- Link to Organisation. No: Leave this to deduplicator
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='Organisation']"/>
                    </xsl:attribute>
                </reference> -->
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Department">

        <xsl:param name="type"/>

        <xsl:variable name="Department" select="col[@field='Department']/text()"/>

        <xsl:if test="$Department!=''">
            <!-- Create the Department -->
            <xsl:variable name="OrgName" select="col[@field='Trainee Organisation']/text()"/>
            <xsl:choose>
                <xsl:when test="$type='reference'">
                    <reference field="department_id" resource="hrm_department">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($OrgName,'/',$Department)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:otherwise>
                    <resource name="hrm_department">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($OrgName,'/',$Department)"/>
                        </xsl:attribute>

                        <data field="name">
                            <xsl:value-of select="$Department"/>
                        </data>

                        <!-- Link to Organisation to filter lookup lists -->
                        <xsl:if test="$OrgName!=''">
                            <reference field="organisation_id" resource="org_organisation">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="concat('ORG:', $OrgName)"/>
                                </xsl:attribute>
                            </reference>
                        </xsl:if>
                    </resource>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Office">

        <xsl:param name="type"/>

        <xsl:variable name="L0" select="col[@field='Office L0']/text()"/>
        
        <xsl:variable name="resourcename">org_office</xsl:variable>
            <!-- @ToDo if-required:
            <xsl:choose>
                <xsl:when test="$OfficeType='Office'">org_office</xsl:when>
                <xsl:when test="$OfficeType='Facility'">org_facility</xsl:when>
                <xsl:when test="$OfficeType='Hospital'">hms_hospital</xsl:when>
                <xsl:when test="$OfficeType='Shelter'">cr_shelter</xsl:when>
                <xsl:when test="$OfficeType='Warehouse'">inv_warehouse</xsl:when>
                <xsl:otherwise>org_office</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>-->

        <xsl:if test="$L0!=''">
            <!-- Create the Office -->
            <xsl:variable name="OrgName" select="col[@field='Trainee Organisation']/text()"/>
            <xsl:variable name="L1" select="col[@field='Office L1']/text()"/>
            <xsl:variable name="L2" select="col[@field='Office L2']/text()"/>
            <xsl:variable name="L3" select="col[@field='Office L3']/text()"/>
            <xsl:variable name="L4" select="col[@field='Office L4']/text()"/>
            <xsl:variable name="L5" select="col[@field='Office L5']/text()"/>

            <xsl:variable name="OfficeName">
                <xsl:choose>
                    <xsl:when test="$L5!=''">
                        <xsl:value-of select="$L5"/>
                    </xsl:when>
                    <xsl:when test="$L4!=''">
                        <xsl:value-of select="$L4"/>
                    </xsl:when>
                    <xsl:when test="$L3!=''">
                        <xsl:value-of select="$L3"/>
                    </xsl:when>
                    <xsl:when test="$L2!=''">
                        <xsl:value-of select="$L2"/>
                    </xsl:when>
                    <xsl:when test="$L1!=''">
                        <xsl:value-of select="$L1"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$L0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:choose>
                <xsl:when test="$type='reference'">
                    <reference field="site_id">
                        <xsl:attribute name="resource">
                            <xsl:value-of select="$resourcename"/>
                        </xsl:attribute>
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($OrgName,'/',$OfficeName)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Country Code = UUID of the L0 Location -->
                    <xsl:variable name="countrycode">
                        <xsl:choose>
                            <xsl:when test="string-length($L0)!=2">
                                <xsl:call-template name="countryname2iso">
                                    <xsl:with-param name="country">
                                        <xsl:value-of select="$L0"/>
                                    </xsl:with-param>
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="uppercase">
                                    <xsl:with-param name="string">
                                       <xsl:value-of select="$L0"/>
                                    </xsl:with-param>
                                </xsl:call-template>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>

                    <resource>
                        <xsl:attribute name="name">
                            <xsl:value-of select="$resourcename"/>
                        </xsl:attribute>
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($OrgName,'/',$OfficeName)"/>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="$OfficeName"/></data>
                        <!-- Link to Organisation -->
                        <reference field="organisation_id" resource="org_organisation">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$OrgName"/>
                            </xsl:attribute>
                        </reference>
                        <!-- Link to Location -->
                        <reference field="location_id" resource="gis_location">
                            <xsl:choose>
                                <xsl:when test="$L5!=''">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="concat('L5/', $countrycode, '/', $L1, '/', $L2, '/', $L3, '/', $L4, '/', $L5)"/>
                                    </xsl:attribute>
                                </xsl:when>
                                <xsl:when test="$L4!=''">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="concat('L4/', $countrycode, '/', $L1, '/', $L2, '/', $L3, '/', $L4)"/>
                                    </xsl:attribute>
                                </xsl:when>
                                <xsl:when test="$L3!=''">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="concat('L3/', $countrycode, '/', $L1, '/', $L2, '/', $L3)"/>
                                    </xsl:attribute>
                                </xsl:when>
                                <xsl:when test="$L2!=''">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="concat('L2/', $countrycode, '/', $L1, '/', $L2)"/>
                                    </xsl:attribute>
                                </xsl:when>
                                <xsl:when test="$L1!=''">
                                    <xsl:attribute name="tuid">
                                        <xsl:value-of select="concat('L1/', $countrycode, '/', $L1)"/>
                                    </xsl:attribute>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:attribute name="uuid">
                                        <xsl:value-of select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>
                                    </xsl:attribute>
                                </xsl:otherwise>
                            </xsl:choose>
                        </reference>
                    </resource>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="JobTitle">

        <xsl:param name="type"/>

        <xsl:variable name="JobName">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$JobTitle"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:if test="$JobName!=''">
            <!-- Create the Job Title -->
            <xsl:variable name="OrgName" select="col[@field='Trainee Organisation']/text()"/>
            <xsl:choose>
                <xsl:when test="$type='reference'">
                    <reference field="job_title_id" resource="hrm_job_title">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($OrgName,'/',$JobName)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:otherwise>
                    <resource name="hrm_job_title">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($OrgName,'/',$JobName)"/>
                        </xsl:attribute>

                        <data field="name">
                            <xsl:value-of select="$JobName"/>
                        </data>

                        <!-- Link to Top-level Organisation to filter lookup lists -->
                        <xsl:if test="$OrgName!=''">
                            <reference field="organisation_id" resource="org_organisation">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="concat('ORG:', $OrgName)"/>
                                </xsl:attribute>
                            </reference>
                        </xsl:if>
                    </resource>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L1">
        <xsl:param name="L0"/>
        <xsl:param name="L1"/>

        <xsl:if test="$L1!=''">

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($L0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$L0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="uppercase">
                            <xsl:with-param name="string">
                               <xsl:value-of select="$L0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L1/', $countrycode, '/', $L1)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$L1"/></data>
                <data field="level"><xsl:text>L1</xsl:text></data>
                <!-- Parent to Country -->
                <xsl:if test="$countrycode!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$country"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L2">
        <xsl:param name="L0"/>
        <xsl:param name="L1"/>
        <xsl:param name="L2"/>

        <xsl:if test="$L2!=''">

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($L0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$L0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="uppercase">
                            <xsl:with-param name="string">
                               <xsl:value-of select="$L0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L2/', $countrycode, '/', $L1, '/', $L2)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$L2"/></data>
                <data field="level"><xsl:text>L2</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="$L1!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $L1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L3">
        <xsl:param name="L0"/>
        <xsl:param name="L1"/>
        <xsl:param name="L2"/>
        <xsl:param name="L3"/>

        <xsl:if test="$L3!=''">

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($L0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$L0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$L0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L3/', $countrycode, '/', $L1, '/', $L2, '/', $L3)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$L3"/></data>
                <data field="level"><xsl:text>L3</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="$L2!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $L1, '/', $L2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$L1!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $L1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L4">
        <xsl:param name="L0"/>
        <xsl:param name="L1"/>
        <xsl:param name="L2"/>
        <xsl:param name="L3"/>
        <xsl:param name="L4"/>

        <xsl:if test="$L4!=''">

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($L0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$L0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$L0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L4/', $countrycode, '/', $L1, '/', $L2, '/', $L3, '/', $L4)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$L4"/></data>
                <data field="level"><xsl:text>L4</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="$L3!=''">
                        <!-- Parent to L3 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3/', $countrycode, '/', $L1, '/', $L2, '/', $L3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$L2!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $L1, '/', $L2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$L1!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $L1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="L5">
        <xsl:param name="L0"/>
        <xsl:param name="L1"/>
        <xsl:param name="L2"/>
        <xsl:param name="L3"/>
        <xsl:param name="L4"/>
        <xsl:param name="L5"/>

        <xsl:if test="$L5!=''">

            <!-- Country Code = UUID of the L0 Location -->
            <xsl:variable name="countrycode">
                <xsl:choose>
                    <xsl:when test="string-length($L0)!=2">
                        <xsl:call-template name="countryname2iso">
                            <xsl:with-param name="country">
                                <xsl:value-of select="$L0"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$L0"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:variable name="country"
                          select="concat('urn:iso:std:iso:3166:-1:code:',
                                         $countrycode)"/>

            <!-- Create the gis location -->
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('L5/', $countrycode, '/', $L1, '/', $L2, '/', $L3, '/', $L4, '/', $L5)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$L5"/></data>
                <data field="level"><xsl:text>L5</xsl:text></data>
                <xsl:choose>
                    <xsl:when test="$L4!=''">
                        <!-- Parent to L4 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L4/', $countrycode, '/', $L1, '/', $L2, '/', $L3, '/', $L4)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$L3!=''">
                        <!-- Parent to L3 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3/', $countrycode, '/', $L1, '/', $L2, '/', $L3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$L2!=''">
                        <!-- Parent to L2 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $L1, '/', $L2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$L1!=''">
                        <!-- Parent to L1 -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $L1)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$countrycode!=''">
                        <!-- Parent to Country -->
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>

        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
