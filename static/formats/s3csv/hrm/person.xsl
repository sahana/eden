<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Human Resources - CSV Import Stylesheet

         2011-04-18 / Dominic König <dominic AT aidiq DOT com>

         Column headers defined in this stylesheet:

         Organisation...................required.....organisation name
         Acronym........................optional.....organisation acronym
         Office.........................required.....office name
         Office Lat.....................optional.....office latitude
         Office Lon.....................optional.....office longitude
         Office Street address..........optional.....office street address
         Office City....................optional.....office city
         Office Post code...............optional.....office post code
         First Name.....................required.....person first name
         Middle Name....................optional.....person middle name
         Last Name......................required.....person last name
         Initials.......................optional.....person initials
         DOB............................optional.....person date of birth
         Skills.........................optional.....comma-separated list of skills
         Email..........................required.....person email address
         Mobile Phone...................optional.....person mobile phone number
         Office Phone...................optional.....office phone number
         Skype..........................optional.....person skype ID
         Home Address...................optional.....person home address
         Job Title......................optional.....job title
         Type...........................optional.....HR type (staff|volunteer)

         Column headers looked up in labels.xml:

         PersonGender...................optional.....person gender

         @todo:

            - add more labels.xml lookups
            - fix location hierarchy:
                - use country name in location_onaccept to match L0?
            - make updateable (don't use temporary UIDs)

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../commons.xsl"/>

    <xsl:param name="mode"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="PersonGender">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">PersonGender</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="orgs"
             match="row"
             use="col[@field='Organisation']"/>

    <xsl:key name="offices"
             match="row"
             use="concat(col[@field='Organisation'], '/', col[@field='Office'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('orgs',
                                                        col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Offices -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('offices',
                                                        concat(col[@field='Organisation'], '/',
                                                               col[@field='Office']))[1])]">
                <xsl:call-template name="Office"/>
            </xsl:for-each>

            <!-- Process all table rows for person records -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OrgName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
            <xsl:choose>
                <xsl:when test="col[@field='Acronym']!=''">
                    <data field="acronym"><xsl:value-of select="col[@field='Acronym']"/></data>
                </xsl:when>
                <!-- this may be totally wrong if the person uses hotmail.com or the like -->
                <xsl:when test="col[@field='Email']!=''">
                    <xsl:variable name="OrgAcronym"
                                  select="substring-before(substring-after(col[@field='Email'],'@'),'.')"/>
                    <data field="acronym"><xsl:value-of select="$OrgAcronym"/></data>
                </xsl:when>
                <!-- no default ! -->
            </xsl:choose>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Office">

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="OfficeName" select="col[@field='Office']/text()"/>

        <resource name="org_office">

            <xsl:attribute name="tuid">
                <xsl:value-of select="$OfficeName"/>
            </xsl:attribute>

            <!-- Office Data -->
            <data field="name"><xsl:value-of select="$OfficeName"/></data>

            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OrgName"/>
                </xsl:attribute>
            </reference>

            <!-- In-line Location Reference -->
            <reference field="location_id" resource="gis_location">
                <resource name="gis_location">
                    <data field="name"><xsl:value-of select="$OfficeName"/></data>
                    <xsl:if test="col[@field='Office Lat']!=''">
                        <data field="lat"><xsl:value-of select="col[@field='Office Lat']"/></data>
                    </xsl:if>
                    <xsl:if test="col[@field='Office Lon']!=''">
                        <data field="lon"><xsl:value-of select="col[@field='Office Lon']"/></data>
                    </xsl:if>
                    <xsl:if test="col[@field='Office Street address']!=''">
                        <data field="addr_street">
                            <xsl:value-of select="concat(
                                                    col[@field='Office Street address'], ', ',
                                                    col[@field='Office City'])"/>
                        </data>
                    </xsl:if>
                    <xsl:if test="col[@field='Office Post code']!=''">
                        <data field="addr_postcode">
                            <xsl:value-of select="col[@field='Office Post code']"/>
                        </data>
                    </xsl:if>
                </resource>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Person Record -->
    <xsl:template match="row">

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="OfficeName" select="col[@field='Office']/text()"/>

        <xsl:variable name="gender">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$PersonGender"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:if test="position()=1">
            <xsl:for-each select="col[starts-with(@name, 'Course')]">
                <xsl:call-template name="Course"/>
            </xsl:for-each>
        </xsl:if>

        <resource name="pr_person">

            <!-- Person record -->
            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
            <data field="middle_name"><xsl:value-of select="col[@field='Middle Name']"/></data>
            <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
            <data field="initials"><xsl:value-of select="col[@field='Initials']"/></data>
            <xsl:if test="col[@field='DOB']">
                <data field="date_of_birth"><xsl:value-of select="col[@field='DOB']"/></data>
            </xsl:if>
            <xsl:if test="$gender!=''">
                <data field="gender">
                    <xsl:attribute name="value"><xsl:value-of select="$gender"/></xsl:attribute>
                </data>
            </xsl:if>

            <!-- Contact Information -->
            <xsl:call-template name="ContactInformation"/>

            <!-- Address -->
            <xsl:call-template name="HomeAddress"/>

            <!-- HR record -->
            <xsl:call-template name="HumanResource">
                <xsl:with-param name="OrgName" select="$OrgName"/>
                <xsl:with-param name="OfficeName" select="$OfficeName"/>
            </xsl:call-template>

            <!-- Competencies -->
            <xsl:call-template name="Competencies">
                <xsl:with-param name="skill_list" select="col[@field='Skills']"/>
            </xsl:call-template>

            <!-- Trainings
            <xsl:call-template name="Trainings"/> -->
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ContactInformation">

        <xsl:if test="col[@field='Email']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="EMAIL"/>
                <data field="value"><xsl:value-of select="col[@field='Email']/text()"/></data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Mobile Phone']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="SMS"/>
                <data field="value"><xsl:value-of select="col[@field='Mobile Phone']/text()"/></data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Office Phone']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="WORK_PHONE"/>
                <data field="value"><xsl:value-of select="col[@field='Office Phone']/text()"/></data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Skype']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="SKYPE"/>
                <data field="value"><xsl:value-of select="col[@field='Skype']/text()"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="HomeAddress">

        <xsl:if test="col[@field='Home Address']!=''">
            <resource name="pr_address">
                <!-- In-line Location Reference -->
                <reference field="location_id" resource="gis_location">
                    <data field="name"><xsl:value-of select="col[@field='Home Address']"/></data>
                    <data field="addr_street">
                        <xsl:value-of select="col[@field='Home Address']"/>
                    </data>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="HumanResource">

        <xsl:param name="OrgName"/>
        <xsl:param name="OfficeName"/>

        <xsl:variable name="type">
            <xsl:choose>
                <xsl:when test="col[@field='Type']='staff' or
                                col[@field='Type']='Staff'">1</xsl:when>
                <xsl:when test="col[@field='Type']='volunteer' or
                                col[@field='Type']='Volunteer'">2</xsl:when>
                <xsl:when test="$mode='staff'">1</xsl:when>
                <xsl:when test="$mode='volunteer'">2</xsl:when>
                <xsl:otherwise>0</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <resource name="hrm_human_resource">

            <!-- HR data -->
            <data field="job_title"><xsl:value-of select="col[@field='Job Title']"/></data>
            <xsl:if test="$type!=0">
                <data field="type"><xsl:value-of select="$type"/></data>
            </xsl:if>

            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OrgName"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Office (staff only) -->
            <xsl:if test="$type=1">
                <reference field="site_id" resource="org_office">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OfficeName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Competencies">

        <xsl:param name="skill_list"/>

        <xsl:if test="$skill_list">
            <xsl:choose>
                <xsl:when test="contains($skill_list, ',')">
                    <xsl:variable name="head" select="normalize-space(substring-before($skill_list, ','))"/>
                    <xsl:variable name="tail" select="substring-after($skill_list, ',')"/>
                    <xsl:call-template name="Competency">
                        <xsl:with-param name="skill" select="$head"/>
                    </xsl:call-template>
                    <xsl:call-template name="Competencies">
                        <xsl:with-param name="skill_list" select="$tail"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="Competency">
                        <xsl:with-param name="skill" select="$skill_list"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Competency">

        <xsl:param name="skill"/>

        <xsl:if test="$skill and $skill!=''">
            <resource name="hrm_competency">
                <reference field="skill_id" resource="hrm_skill">
                    <resource name="hrm_skill">
                        <data field="name"><xsl:value-of select="$skill"/></data>
                    </resource>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Pull this in from training_event.xsl if-required
    <xsl:template name="Course">

        <xsl:variable name="CourseName" select="normalize-space(substring-after(@name, ':'))"/>
        <resource name="hrm_course">
            <xsl:attribute name="tuid"><xsl:value-of select="$CourseName"/></xsl:attribute>
            <data field="name"><xsl:value-of select="$CourseName"/></data>
        </resource>

    </xsl:template> -->

    <!-- ****************************************************************** -->
    <!-- Pull this in from training_event.xsl if-required
    <xsl:template name="Trainings">

        <xsl:for-each select="col[starts-with(@name, 'Course')]">
            <xsl:variable name="CourseName" select="normalize-space(substring-after(@field, ':'))"/>
            <xsl:variable name="Dates" select="normalize-space(text())"/>
            <xsl:if test="$Dates!=''">
                <resource name="hrm_training">
                    <reference field="course_id" resource="hrm_course">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$CourseName"/>
                        </xsl:attribute>
                    </reference>
                    <xsl:choose>
                        <xsl:when test="$Dates='Y' or $Dates='y'"/>
                        <xsl:when test="contains($Dates, '-')">
                            <xsl:variable name="StartDate" select="normalize-space(substring-before($Dates, '-'))"/>
                            <xsl:variable name="tail" select="normalize-space(substring-after($Dates, '-'))"/>
                            <xsl:variable name="EndDate">
                                <xsl:choose>
                                    <xsl:when test="contains(tail, '(')">
                                        <xsl:value-of select="normalize-space(substring-before($tail, '('))"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="$tail"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:variable>
                            <xsl:variable name="Place">
                                <xsl:choose>
                                    <xsl:when test="contains(tail, '(')">
                                        <xsl:value-of select="normalize-space(substring-before(substring-after($tail, '('), ')'))"/>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="''"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:variable>
                            <xsl:if test="$StartDate!=''">
                                <data field="start_date"><xsl:value-of select="$StartDate"/></data>
                                <xsl:if test="$EndDate!=''">
                                    <data field="end_date"><xsl:value-of select="$EndDate"/></data>
                                </xsl:if>
                            </xsl:if>
                            <xsl:if test="$Place!=''">
                                <data field="place"><xsl:value-of select="Place"/></data>
                            </xsl:if>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:variable name="Date" select="normalize-space(substring-before($Dates, '-'))"/>
                            <xsl:if test="$Date!=''">
                                <data field="start_date"><xsl:value-of select="$Date"/></data>
                                <data field="end_date"><xsl:value-of select="$Date"/></data>
                            </xsl:if>
                        </xsl:otherwise>
                    </xsl:choose>
                </resource>
            </xsl:if>
        </xsl:for-each>

    </xsl:template> -->

    <!-- ****************************************************************** -->
</xsl:stylesheet>
