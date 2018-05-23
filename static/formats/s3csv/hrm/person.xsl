<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Human Resources - CSV Import Stylesheet
         Must be imported through the pr_person resource

         Column headers defined in this stylesheet:

         Organisation...................required.....organisation name
         Branch.........................optional.....branch organisation name
         ...SubBranch,SubSubBranch...etc (indefinite depth, must specify all from root)

         Type...........................optional.....HR type (staff|volunteer|member)
         Office.........................optional.....Facility name
         OrgGroup.......................optional.....OrgGroup name
         Facility Type..................optional.....Office, Facility, Hospital, Shelter, Warehouse
         Office Lat.....................optional.....office latitude
         Office Lon.....................optional.....office longitude
         Office Street address..........optional.....office street address
         Office Postcode................optional.....office postcode
         Department.....................optional.....human_resource.department
         Job Title......................optional.....human_resource.job_title
         Contract Term..................optional.....hrm_contract.term (short-term|long-term|permanent)
         Hours Model....................optional.....hrm_contract.hours (part-time|full-time)
         Staff Level....................optional.....salary.staff_level_id
         Salary Grade...................optional.....salary.salary_grade_id
         Monthly Salary.................optional.....salary.monthly_amount
         Salary Start Date..............optional.....salary.start_date
         Salary End Date................optional.....salary.end_date
         Status.........................optional.....human_resource.status
         Start Date.....................optional.....human_resource start date
         First Name.....................required.....person first name
         Middle Name....................optional.....person middle name
         Last Name......................optional.....person last name (required in some deployments)
         Initials.......................optional.....person initials
         DOB............................optional.....person date of birth
         Nationality....................optional.....person_details nationality
         Occupation.....................optional.....person_details occupation
         Company........................optional.....person_details company
         Affiliations............ ......optional.....person_details affiliation
         Marital Status.................optional.....person_details marital status
         Number of Children.............optional.....person_details number of children
         Place of Birth.................optional.....person_details place of birth
         Father Name....................optional.....person_details father name
         Mother Name....................optional.....person_details mother name
         Grandfather Name...............optional.....person_details grandfather name
         Grandmother Name...............optional.....person_details grandmother name
         Religion.......................optional.....person_details religion
         Criminal Record................optional.....person_details criminal record
         Military Service...............optional.....person_details military service
         Blood Type.....................optional.....pr_physical_description blood_type
         Ethnicity......................optional.....pr_physical_description ethnicity
         National ID....................optional.....person identity type = 2, value
         Passport No....................optional.....person identity type = 1, value
         Passport Country...............optional.....person identity
         Passport Expiry Date...........optional.....person identity
         Email..........................required.....person email address. Supports multiple comma-separated
         Mobile Phone...................optional.....person mobile phone number. Supports multiple comma-separated
         Home Phone.....................optional.....home phone number
         Office Phone...................optional.....office phone number
         Skype..........................optional.....person skype ID
         Twitter........................optional.....person Twitter handle
         Callsign.......................optional.....person Radio Callsign
         Emergency Contact Name.........optional.....pr_contact_emergency name
         Emergency Contact Relationship.optional.....pr_contact_emergency relationship
         Emergency Contact Phone........optional.....pr_contact_emergency phone
         Social Insurance Number........optional.....hrm_insurance.insurance_number
         Social Insurance Place.........optional.....hrm_insurance.insurer
         Health Insurance Number........optional.....hrm_insurance.insurance_number
         Health Care Provider...........optional.....hrm_insurance.provider
         Home Postcode..................optional.....person home address postcode
         Home Lat.......................optional.....person home address latitude
         Home Lon.......................optional.....person home address longitude
         Home Country...................optional.....person home address Country
         Home L1........................optional.....person home address L1
         Home L2........................optional.....person home address L2
         Home L3........................optional.....person home address L3
         Home L4........................optional.....person home address L4
         Permanent Address..............optional.....person permanent address
         Permanent Postcode.............optional.....person permanent address postcode
         Permanent Lat..................optional.....person permanent address latitude
         Permanent Lon..................optional.....person permanent address longitude
         Permanent Country..............optional.....person permanent address Country
         Permanent L1...................optional.....person permanent address L1
         Permanent L2...................optional.....person permanent address L2
         Permanent L3...................optional.....person permanent address L3
         Permanent L4...................optional.....person permanent address L4
         Skills.........................optional.....comma-separated list of Skills
         Teams..........................optional.....comma-separated list of Groups
         Trainings......................optional.....comma-separated list of Training Courses attended
         Training:XXXX..................optional.....Date of Training Course XXXX OR "True" to add Training Courses by column
                                                     Can be Date;Venue in field to specify the Venue of the Training Event
         External Trainings.............optional.....comma-separated list of External Training Courses attended
         Certificates...................optional.....comma-separated list of Certificates
         Certificate:XXXX...............optional.....Expiry Date of Certificate XXXX OR "True" to add Certificate by column
         Education Level................optional.....person education level of award (highest)
         Degree Name....................optional.....person education award
         Major..........................optional.....person education major
         Grade..........................optional.....person education grade
         Year...........................optional.....person education year
         Institute......................optional.....person education institute
         Award Type.....................optional.....hrm_award.award_type_id
         Award Date.....................optional.....hrm_award.date
         Awarding Body..................optional.....hrm_award.awarding_body
         Disciplinary Type..............optional.....hrm_disciplinary_action.disciplinary_type_id
         Disciplinary Date..............optional.....hrm_disciplinary_action.date
         Disciplinary Body..............optional.....hrm_disciplinary_action.disciplinary_body
         Active.........................optional.....volunteer_details.active
         Volunteer Type.................optional.....volunteer_details.volunteer_type
         Availability...................optional.....Availability dropdown
         Availability Comments..........optional.....Availability Comments
         Slot:XXXX......................optional.....Availability for Slot XXXX
         Comments.......................optional.....hrm_human_resource.comments

         Extensions for deploy module:
         Deployable.....................optional.....link to deployments module (organisation name|true)
         Deployable Roles...............optional.....credentials (job_titles for which person is deployable)
         Deployments....................optional.....comma-separated list of Missions for which the person was deployed

         Turkey-specific:
         Identity Card City
         Identity Card Town
         Identity Card District
         Identity Card Volume No
         Identity Card Family Order No
         Identity Card Order No

         PHRC-specific:
         Volunteer Cluster Type.........optional.....volunteer_cluster cluster_type name
         Volunteer Cluster..............optional.....volunteer_cluster cluster name
         Volunteer Cluster Position.....optional.....volunteer_cluster cluster_position name

         Column headers looked up in labels.xml:

         HomeAddress....................optional.....Home Street Address
         JobTitle.......................optional.....HR Job Title/Volunteer Role/Position
         HRMType........................optional.....
         MemberType.....................optional.....
         PersonGender...................optional.....person gender
         StaffID........................optional.....Staff ID/Volunteer ID

         @ToDo:
            - add more labels.xml lookups
            - fix location hierarchy:
                - use country name in location_onaccept to match L0?
            - make updateable (don't use temporary UIDs)

    *********************************************************************** -->
    <xsl:import href="award.xsl"/>
    <xsl:import href="contract.xsl"/>
    <xsl:import href="disciplinary.xsl"/>
    <xsl:import href="insurance.xsl"/>
    <xsl:import href="salary.xsl"/>
    <xsl:import href="org_group_person.xsl"/>

    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:variable name="TeamPrefix" select="'Team:'"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="HomeAddress">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">HomeAddress</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="HRMType">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">HRMType</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="JobTitle">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">JobTitle</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="MemberType">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">MemberType</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="OrgGroupHeaders">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">OrgGroup</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="PersonGender">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">PersonGender</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="StaffID">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">StaffID</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->

    <xsl:key name="awardtypes" match="row"
             use="col[@field='Award Type']"/>

    <xsl:key name="departments" match="row"
             use="concat(col[@field='Organisation'], '/', col[@field='Department'])"/>

    <xsl:key name="disciplinarytypes" match="row"
             use="col[@field='Disciplinary Type']"/>

    <xsl:key name="education_level" match="row"
             use="col[@field='Education Level']"/>

    <xsl:key name="jobtitles" match="row"
             use="concat(col[@field='Organisation'], '/',
                         col[contains(
                             document('../labels.xml')/labels/column[@name='JobTitle']/match/text(),
                             concat('|', @field, '|'))])"/>

    <xsl:key name="missions" match="row"
             use="col[@field='Deployments']"/>

    <xsl:key name="orgs" match="row"
             use="col[@field='Deployable']"/>

    <xsl:key name="orggroups" match="row"
             use="col[contains(document('../labels.xml')/labels/column[@name='OrgGroup']/match/text(),
                               concat('|', @field, '|'))]"/>

    <xsl:key name="salarygrades" match="row"
             use="col[@field='Salary Grade']"/>

    <xsl:key name="stafflevels" match="row"
             use="col[@field='Staff Level']"/>

    <xsl:key name="volunteerclustertypes" match="row"
             use="col[@field='Volunteer Cluster Type']"/>

    <xsl:key name="volunteerclusters" match="row"
             use="concat(col[@field='Volunteer Cluster Type'],
                         col[@field='Volunteer Cluster'])"/>

    <xsl:key name="volunteerclusterpositions" match="row"
             use="col[@field='Volunteer Cluster Position']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Import the Organisation hierarchy -->
            <xsl:for-each select="table/row[1]">
                <xsl:call-template name="OrganisationHierarchy">
                    <xsl:with-param name="level">Organisation</xsl:with-param>
                    <xsl:with-param name="rows" select="//table/row"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Deployable Orgs -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('orgs',
                                                                       col[@field='Deployable'])[1])]">
                <xsl:call-template name="DeployableOrg">
                    <xsl:with-param name="Field">Deployable</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Org Groups -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('orggroups',
                                            col[contains(document('../labels.xml')/labels/column[@name='OrgGroup']/match/text(),
                                                         concat('|', @field, '|'))])[1])]">
                <xsl:call-template name="OrgGroup">
                    <xsl:with-param name="Field" select="$OrgGroupHeaders"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Departments -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('departments',
                                                        concat(col[@field='Organisation'], '/',
                                                               col[@field='Department']))[1])]">
                <xsl:call-template name="Department">
                    <xsl:with-param name="type">resource</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Job Titles -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('jobtitles',
                                            concat(col[@field='Organisation'], '/',
                                                   col[contains(
                                                       document('../labels.xml')/labels/column[@name='JobTitle']/match/text(),
                                                       concat('|', @field, '|'))])
                                        )[1])]">
                <xsl:call-template name="JobTitle">
                    <xsl:with-param name="type">resource</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Availability Slots -->
            <xsl:for-each select="table/row[1]">
                <xsl:for-each select="col[starts-with(@field, 'Slot')]">
                    <xsl:call-template name="Slot"/>
                </xsl:for-each>
            </xsl:for-each>

            <!-- Award Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('awardtypes',
                                                                       col[@field='Award Type'])[1])]">
                <xsl:call-template name="AwardType">
                    <xsl:with-param name="Field">Award Type</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Disciplinary Action Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('disciplinarytypes',
                                                                       col[@field='Disciplinary Type'])[1])]">
                <xsl:call-template name="DisciplinaryActionType">
                    <xsl:with-param name="Field">Disciplinary Type</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Education Levels -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('education_level',
                                                                   col[@field='Education Level'])[1])]">
                <xsl:call-template name="EducationLevel"/>
            </xsl:for-each>

            <!-- Missions -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('missions',
                                                                   col[@field='Deployments'])[1])]">
                <xsl:call-template name="splitList">
                    <xsl:with-param name="list" select="col[@field='Deployments']"/>
                    <xsl:with-param name="arg">mission</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Salary Grades -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('salarygrades',
                                                                       col[@field='Salary Grade'])[1])]">
                <xsl:call-template name="SalaryGrade">
                    <xsl:with-param name="Field">Salary Grade</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Staff Levels -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('stafflevels',
                                                                       col[@field='Staff Level'])[1])]">
                <xsl:call-template name="StaffLevel">
                    <xsl:with-param name="Field">Staff Level</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Volunteer Clusters -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('volunteerclusters',
                                                                       concat(col[@field='Volunteer Cluster Type'],
                                                                              col[@field='Volunteer Cluster']))[1])]">
                <xsl:call-template name="VolunteerCluster"/>
            </xsl:for-each>

            <!-- Volunteer Cluster Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('volunteerclustertypes',
                                                                       col[@field='Volunteer Cluster Type'])[1])]">
                <xsl:call-template name="VolunteerClusterType"/>
            </xsl:for-each>

            <!-- Volunteer Cluster Positions -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('volunteerclusterpositions',
                                                                       col[@field='Volunteer Cluster Position'])[1])]">
                <xsl:call-template name="VolunteerClusterPosition"/>
            </xsl:for-each>

            <!-- Process all table rows for person records -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Department">

        <xsl:param name="type"/>

        <xsl:variable name="Department" select="col[@field='Department']/text()"/>
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <xsl:if test="$Department!=''">
            <!-- Create the Department -->
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
    <xsl:template name="JobTitle">

        <xsl:param name="type"/>

        <xsl:variable name="JobName">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$JobTitle"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <xsl:if test="$JobName!=''">
            <!-- Create the Job Title -->
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
    <!-- Template to import the Organisation hierarchy, to be called only once for the first row -->

    <xsl:template name="OrganisationHierarchy">

        <xsl:param name="level"/>
        <xsl:param name="rows"/>
        <xsl:param name="parentID"/>

        <!-- Get the next level -->
        <xsl:variable name="nextLevel">
            <xsl:call-template name="NextLevel">
                <xsl:with-param name="level" select="$level"/>
            </xsl:call-template>
        </xsl:variable>

        <!-- Get the name -->
        <xsl:variable name="name" select="col[@field=$level]/text()"/>

        <!-- Generate the tuid -->
        <xsl:variable name="tuid">
            <xsl:choose>
                <xsl:when test="$parentID and $parentID!=''">
                    <xsl:value-of select="concat($parentID, '/', $name)"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="concat('ORG:', $name)"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <!-- Create this Organisation -->
        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$tuid"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$name"/></data>
            <xsl:if test="$parentID and $parentID!=''">
                <resource name="org_organisation_branch" alias="parent">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$parentID"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
        </resource>

        <!-- Create all offices for this organisation -->
        <xsl:for-each select="$rows[col[@field=$level]/text()=$name and
                                    (not(col[@field=$nextLevel]/text()) or col[@field=$nextLevel]/text()='') and
                                    col[@field='Office']/text()!='']">

            <xsl:variable name="OfficeName" select="col[@field='Office']"/>
            <xsl:if test="generate-id(.)=generate-id($rows[col[@field=$level]/text()=$name and
                                                           (not(col[@field=$nextLevel]/text()) or col[@field=$nextLevel]/text()='') and
                                                           col[@field='Office']/text()=$OfficeName][1])">
                <xsl:call-template name="Office"/>
            </xsl:if>
        </xsl:for-each>

        <!-- Process Branches -->
        <xsl:for-each select="$rows[col[@field=$level]/text()=$name and col[@field=$nextLevel]/text()!=''][1]">
            <xsl:call-template name="OrganisationHierarchy">
                <xsl:with-param name="rows" select="$rows[col[@field=$level]/text()=$name and col[@field=$nextLevel]/text()!='']"/>
                <xsl:with-param name="level" select="$nextLevel"/>
                <xsl:with-param name="parentID" select="$tuid"/>
            </xsl:call-template>
        </xsl:for-each>

        <!-- Process Siblings -->
        <xsl:for-each select="$rows[col[@field=$level]/text()!=$name][1]">
            <xsl:call-template name="OrganisationHierarchy">
                <xsl:with-param name="rows" select="$rows[col[@field=$level]/text()!=$name]"/>
                <xsl:with-param name="level" select="$level"/>
                <xsl:with-param name="parentID" select="$parentID"/>
            </xsl:call-template>
        </xsl:for-each>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Template to generate an organisation tuid for the current row -->

    <xsl:template name="OrganisationID">

        <xsl:param name="parentID"/>
        <xsl:param name="parentLevel"/>
        <xsl:param name="prefix">ORG:</xsl:param>
        <xsl:param name="suffix"/>

        <xsl:variable name="level">
            <xsl:call-template name="NextLevel">
                <xsl:with-param name="level" select="$parentLevel"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="name" select="col[@field=$level]/text()"/>
        <xsl:choose>
            <xsl:when test="$name!=''">
                <xsl:variable name="id">
                    <xsl:choose>
                        <xsl:when test="$parentID and $parentID!=''">
                            <xsl:value-of select="concat($parentID, '/', $name)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="concat($prefix, $name)"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:call-template name="OrganisationID">
                    <xsl:with-param name="parentID" select="$id"/>
                    <xsl:with-param name="parentLevel" select="$level"/>
                    <xsl:with-param name="prefix" select="$prefix"/>
                    <xsl:with-param name="suffix" select="$suffix"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="concat($parentID, $suffix)"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Template to generate the name of the next level column -->

    <xsl:template name="NextLevel">

        <xsl:param name="level"/>
        <xsl:choose>
            <xsl:when test="not($level) or $level=''">Organisation</xsl:when>
            <xsl:when test="$level='Organisation'">Branch</xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="concat('Sub', $level)"/>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Office">

        <xsl:variable name="OfficeName" select="col[@field='Office']/text()"/>
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
        <xsl:if test="$OfficeName!=''">
            <resource>
                <xsl:attribute name="name">
                    <xsl:value-of select="$resourcename"/>
                </xsl:attribute>
                <xsl:attribute name="tuid">
                    <xsl:call-template name="OrganisationID">
                        <xsl:with-param name="prefix">OFFICE:</xsl:with-param>
                        <xsl:with-param name="suffix" select="concat('/', $OfficeName)"/>
                    </xsl:call-template>
                </xsl:attribute>

                <!-- Name field is limited to 64 chars -->
                <data field="name"><xsl:value-of select="substring($OfficeName,1,64)"/></data>

                <!-- Link to Organisation -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:call-template name="OrganisationID"/>
                    </xsl:attribute>
                </reference>

                <xsl:choose>
                    <!-- Don't create null locations which over-write good locations imported via office.csv -->
                    <xsl:when test="col[@field='Office Street address'] or col[@field='Office Lat']">
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
                                        <xsl:value-of select="col[@field='Office Street address']"/>
                                    </data>
                                </xsl:if>
                                <xsl:if test="col[@field='Office Postcode']!=''">
                                    <data field="addr_postcode">
                                        <xsl:value-of select="col[@field='Office Postcode']"/>
                                    </data>
                                </xsl:if>
                            </resource>
                        </reference>
                    </xsl:when>
                </xsl:choose>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Person Record -->
    <xsl:template match="row">

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="BloodType" select="col[@field='Blood Type']"/>
        <xsl:variable name="Ethnicity" select="col[@field='Ethnicity']"/>
        <xsl:variable name="Teams" select="col[@field='Teams']"/>
        <xsl:variable name="Trainings" select="col[@field='Trainings']"/>
        <xsl:variable name="TrainingsExternal" select="col[@field='External Trainings']"/>
        <xsl:variable name="Certificates" select="col[@field='Certificates']"/>
        <xsl:variable name="DeployableRoles" select="col[@field='Deployable Roles']"/>

        <xsl:variable name="gender">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$PersonGender"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="home">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$HomeAddress"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="type">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$HRMType"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="member">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$MemberType"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:variable name="staffID">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$StaffID"/>
            </xsl:call-template>
        </xsl:variable>

<!--        <xsl:if test="position()=1">
            <xsl:for-each select="col[starts-with(@name, 'Course')]">
                <xsl:call-template name="Course"/>
            </xsl:for-each>
        </xsl:if>-->

        <resource name="pr_person">

            <xsl:variable name="person_tuid" select="concat('Person:', position())"/>
            <xsl:attribute name="tuid">
                <xsl:value-of select="$person_tuid"/>
            </xsl:attribute>

            <!-- Person record -->
            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
            <xsl:if test="col[@field='Middle Name']!=''">
                <data field="middle_name"><xsl:value-of select="col[@field='Middle Name']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Last Name']!=''">
                <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Initials']!=''">
                <data field="initials"><xsl:value-of select="col[@field='Initials']"/></data>
            </xsl:if>
            <xsl:if test="col[@field='DOB']!=''">
                <data field="date_of_birth"><xsl:value-of select="col[@field='DOB']"/></data>
            </xsl:if>
            <xsl:if test="$gender!=''">
                <data field="gender">
                    <xsl:attribute name="value"><xsl:value-of select="$gender"/></xsl:attribute>
                </data>
            </xsl:if>

            <resource name="pr_person_details">
                <xsl:if test="col[@field='Marital Status']!=''">
                    <data field="marital_status"><xsl:value-of select="col[@field='Marital Status']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Place of Birth']!=''">
                    <data field="place_of_birth"><xsl:value-of select="col[@field='Place of Birth']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Father Name']!=''">
                    <data field="father_name"><xsl:value-of select="col[@field='Father Name']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Mother Name']!=''">
                    <data field="mother_name"><xsl:value-of select="col[@field='Mother Name']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Grandfather Name']!=''">
                    <data field="grandfather_name"><xsl:value-of select="col[@field='Grandfather Name']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Grandmother Name']!=''">
                    <data field="grandmother_name"><xsl:value-of select="col[@field='Grandmother Name']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Number of Children']!=''">
                    <data field="number_children"><xsl:value-of select="col[@field='Number of Children']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Military Service']!=''">
                    <data field="military_service"><xsl:value-of select="col[@field='Military Service']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Criminal Record']!=''">
                    <data field="criminal_record"><xsl:value-of select="col[@field='Criminal Record']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Religion']!=''">
	                <data field="religion">
                        <xsl:call-template name="lowercase">
                            <xsl:with-param name="string">
                               <xsl:value-of select="col[@field='Religion']"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </data>
	            </xsl:if>
	            <xsl:variable name="l0">
                    <xsl:choose>
                        <xsl:when test="col[@field='Nationality']!=''">
                            <xsl:value-of select="col[@field='Nationality']"/>
                        </xsl:when>
                        <xsl:when test="col[@field='Passport Country']!=''">
                            <xsl:value-of select="col[@field='Passport Country']"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="countrycode">
                    <xsl:choose>
                        <xsl:when test="string-length($l0)!=2">
                            <xsl:call-template name="countryname2iso">
                                <xsl:with-param name="country">
                                    <xsl:value-of select="$l0"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="uppercase">
                                <xsl:with-param name="string">
                                   <xsl:value-of select="$l0"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:if test="$countrycode!=''">
                    <data field="nationality">
                        <xsl:value-of select="$countrycode"/>
                    </data>
	            </xsl:if>
                <xsl:if test="col[@field='Occupation']!=''">
                    <data field="occupation"><xsl:value-of select="col[@field='Occupation']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Company']!=''">
                    <data field="company"><xsl:value-of select="col[@field='Company']"/></data>
	            </xsl:if>
                <xsl:if test="col[@field='Affiliations']!=''">
                    <data field="affiliations"><xsl:value-of select="col[@field='Affiliations']"/></data>
                </xsl:if>
            </resource>

            <!-- Turkish Identity -->
            <resource name="tr_identity">
                <xsl:variable name="id_l3">
                    <xsl:value-of select="col[@field='Identity Card District']"/>
                </xsl:variable>
                <xsl:if test="$id_l3!=''">
                    <reference field="location_id" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Location L3: ', $id_l3)"/>
                        </xsl:attribute>
                    </reference>
                   </xsl:if>
                <xsl:if test="col[@field='Identity Card Volume No']!=''">
                    <data field="volume_no"><xsl:value-of select="col[@field='Identity Card Volume No']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Identity Card Family Order No']!=''">
                    <data field="family_order_no"><xsl:value-of select="col[@field='Identity Card Family Order No']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Identity Card Order No']!=''">
                    <data field="order_no"><xsl:value-of select="col[@field='Identity Card Order No']"/></data>
                </xsl:if>
            </resource>

            <xsl:if test="$BloodType!='' or $Ethnicity!=''">
                <resource name="pr_physical_description">
                    <xsl:if test="$Ethnicity!=''">
                        <data field="ethnicity"><xsl:value-of select="$Ethnicity"/></data>
                    </xsl:if>
                    <xsl:if test="$BloodType!=''">
                        <data field="blood_type">
                            <xsl:choose>
                                <xsl:when test="$BloodType='0+'">
                                    <xsl:text>O+</xsl:text>
                                </xsl:when>
                                <xsl:when test="$BloodType='0-'">
                                    <xsl:text>O-</xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:value-of select="$BloodType"/>
                                </xsl:otherwise>
                            </xsl:choose>
                        </data>
                    </xsl:if>
                </resource>
            </xsl:if>

            <!-- Identity Information -->
            <xsl:call-template name="IdentityInformation"/>

            <!-- Contact Information -->
            <xsl:call-template name="ContactInformation"/>

            <!-- Addresses -->
            <xsl:if test="$home!='' or col[@field='Home Postcode']!='' or col[@field='Home L4']!='' or col[@field='Home L3']!='' or col[@field='Home L2']!='' or col[@field='Home L1']!=''">
                <xsl:call-template name="Address">
                    <xsl:with-param name="type">1</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <xsl:if test="col[@field='Permanent Address']!='' or col[@field='Permanent Postcode']!='' or col[@field='Permanent L4']!='' or col[@field='Permanent L3']!='' or col[@field='Permanent L2']!='' or col[@field='Permanent L1']!=''">
                <xsl:call-template name="Address">
                    <xsl:with-param name="type">2</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <!-- HR record -->
            <xsl:choose>
                <xsl:when test="$type='3'">
                    <xsl:call-template name="Member">
                        <xsl:with-param name="type" select="$member"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="HumanResource">
                        <xsl:with-param name="FacilityType" select="col[@field='Facility Type']/text()"/>
                        <xsl:with-param name="OfficeName" select="col[@field='Office']/text()"/>
                        <xsl:with-param name="StaffID" select="$staffID"/>
                        <xsl:with-param name="Status">
                            <xsl:call-template name="lowercase">
                                <xsl:with-param name="string" select="col[@field='Status']"/>
                            </xsl:call-template>
                        </xsl:with-param>
                        <xsl:with-param name="type" select="$type"/>
                        <xsl:with-param name="person_tuid" select="$person_tuid"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>

            <!-- Link to OrgGroup -->
            <xsl:call-template name="OrgGroupPerson">
                <xsl:with-param name="Field" select="$OrgGroupHeaders"/>
            </xsl:call-template>

            <!-- Education -->
            <xsl:call-template name="Education">
                <xsl:with-param name="level" select="col[@field='Education Level']"/>
                <xsl:with-param name="name" select="col[@field='Degree Name']"/>
                <xsl:with-param name="major" select="col[@field='Major']"/>
                <xsl:with-param name="grade" select="col[@field='Grade']"/>
                <xsl:with-param name="year" select="col[@field='Year']"/>
                <xsl:with-param name="institute" select="col[@field='Institute']"/>
            </xsl:call-template>

            <!-- Competencies -->
            <xsl:call-template name="Competencies">
                <xsl:with-param name="skill_list" select="col[@field='Skills']"/>
            </xsl:call-template>

            <!-- Awards -->
            <xsl:if test="col[@field='Award Type']/text() != ''">
                <xsl:call-template name="Award">
                    <xsl:with-param name="person_tuid" select="$person_tuid"/>
                </xsl:call-template>
            </xsl:if>

            <!-- Disciplinary Record -->
            <xsl:if test="col[@field='Disciplinary Type']/text() != ''">
                <xsl:call-template name="DisciplinaryAction">
                    <xsl:with-param name="person_tuid" select="$person_tuid"/>
                </xsl:call-template>
            </xsl:if>

            <!-- Job Roles that a deployable is credentialled for -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list" select="$DeployableRoles"/>
                <xsl:with-param name="arg">deployablerole_ref</xsl:with-param>
            </xsl:call-template>

            <!-- Teams -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list" select="$Teams"/>
                <xsl:with-param name="arg">team</xsl:with-param>
            </xsl:call-template>

            <!-- Trainings -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list" select="$Trainings"/>
                <xsl:with-param name="arg">training</xsl:with-param>
                <xsl:with-param name="org" select="$OrgName"/>
            </xsl:call-template>

            <!-- External Trainings -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list" select="$TrainingsExternal"/>
                <xsl:with-param name="arg">training</xsl:with-param>
                <xsl:with-param name="arg2">T</xsl:with-param>
                <!-- Org still present for filtering -->
                <xsl:with-param name="org" select="$OrgName"/>
            </xsl:call-template>

            <!-- Training:XXXX -->
            <xsl:for-each select="col[starts-with(@field, 'Training:')]">
                <xsl:variable name="Date" select="text()"/>
                <xsl:if test="$Date!=''">
                    <xsl:call-template name="resource">
                        <xsl:with-param name="item" select="normalize-space(substring-after(@field, ':'))"/>
                        <xsl:with-param name="arg">training</xsl:with-param>
                        <xsl:with-param name="date" select="$Date"/>
                        <xsl:with-param name="org" select="$OrgName"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:for-each>
<!--
            <xsl:call-template name="Trainings">
                <xsl:with-param name="course_list" select="col[@field='Trainings']"/>
            </xsl:call-template>
-->

            <!-- Availability -->
            <xsl:call-template name="Availability"/>

            <!-- Certificates -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list" select="$Certificates"/>
                <xsl:with-param name="arg">certificate</xsl:with-param>
            </xsl:call-template>

            <!-- Certificate:XXXX -->
            <xsl:for-each select="col[starts-with(@field, 'Certificate:')]">
                <xsl:variable name="Date" select="text()"/>
                <xsl:if test="$Date!=''">
                    <xsl:call-template name="resource">
                        <xsl:with-param name="item" select="normalize-space(substring-after(@field, ':'))"/>
                        <xsl:with-param name="arg">certificate</xsl:with-param>
                        <xsl:with-param name="date" select="$Date"/>
                    </xsl:call-template>
                </xsl:if>
            </xsl:for-each>
        </resource>

        <!-- Job Roles that a deployable is credentialled for -->
        <xsl:call-template name="splitList">
            <xsl:with-param name="list" select="$DeployableRoles"/>
            <xsl:with-param name="arg">deployablerole</xsl:with-param>
        </xsl:call-template>

        <!-- Locations -->
        <xsl:if test="$home!='' or col[@field='Home Postcode']!='' or col[@field='Home L4']!='' or col[@field='Home L3']!='' or col[@field='Home L2']!='' or col[@field='Home L1']!=''">
            <xsl:call-template name="Locations">
                <xsl:with-param name="address" select="$home"/>
                <xsl:with-param name="postcode" select="col[@field='Home Postcode']/text()"/>
                <xsl:with-param name="type">1</xsl:with-param>
                <xsl:with-param name="l0" select="col[@field='Home Country']/text()"/>
                <xsl:with-param name="l1" select="col[@field='Home L1']/text()"/>
                <xsl:with-param name="l2" select="col[@field='Home L2']/text()"/>
                <xsl:with-param name="l3" select="col[@field='Home L3']/text()"/>
                <xsl:with-param name="l4" select="col[@field='Home L4']/text()"/>
                <xsl:with-param name="l5" select="col[@field='Home L5']/text()"/>
                <xsl:with-param name="lat" select="col[@field='Home Lat']/text()"/>
                <xsl:with-param name="lon" select="col[@field='Home Lon']/text()"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="col[@field='Permanent Address']!='' or col[@field='Permanent Postcode']!='' or col[@field='Permanent L4']!='' or col[@field='Permanent L3']!='' or col[@field='Permanent L2']!='' or col[@field='Permanent L1']!=''">
            <xsl:call-template name="Locations">
                <xsl:with-param name="address" select="col[@field='Permanent Address']/text()"/>
                <xsl:with-param name="postcode" select="col[@field='Permanent Postcode']/text()"/>
                <xsl:with-param name="type">2</xsl:with-param>
                <xsl:with-param name="l0" select="col[@field='Permanent Country']/text()"/>
                <xsl:with-param name="l1" select="col[@field='Permanent L1']/text()"/>
                <xsl:with-param name="l2" select="col[@field='Permanent L2']/text()"/>
                <xsl:with-param name="l3" select="col[@field='Permanent L3']/text()"/>
                <xsl:with-param name="l4" select="col[@field='Permanent L4']/text()"/>
                <xsl:with-param name="l5" select="col[@field='Permanent L5']/text()"/>
                <xsl:with-param name="lat" select="col[@field='Permanent Lat']/text()"/>
                <xsl:with-param name="lon" select="col[@field='Permanent Lon']/text()"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="col[@field='Identity Card District']!=''">
            <xsl:call-template name="TR_ID_Locations">
                <xsl:with-param name="l1" select="col[@field='Identity Card City']/text()"/>
                <xsl:with-param name="l2" select="col[@field='Identity Card Town']/text()"/>
                <xsl:with-param name="l3" select="col[@field='Identity Card District']/text()"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Member">

        <xsl:param name="type"/>

        <resource name="member_membership">

            <!-- Member data -->
            <xsl:if test="col[@field='Start Date']!=''">
                <data field="start_date"><xsl:value-of select="col[@field='Start Date']"/></data>
            </xsl:if>
            <xsl:if test="$type!=0 or $type!=''">
                <data field="type"><xsl:value-of select="$type"/></data>
            </xsl:if>

            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:call-template name="OrganisationID"/>
                </xsl:attribute>
            </reference>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="HumanResource">

        <xsl:param name="FacilityType"/>
        <xsl:param name="OfficeName"/>
        <xsl:param name="person_tuid"/>
        <xsl:param name="StaffID"/>
        <xsl:param name="Status"/>
        <xsl:param name="type"/>

        <xsl:variable name="Deployable" select="col[@field='Deployable']/text()"/>

        <resource name="hrm_human_resource">

            <!-- HR data -->
            <xsl:if test="$StaffID!=''">
                <data field="code"><xsl:value-of select="$StaffID"/></data>
            </xsl:if>
            <xsl:if test="col[@field='Start Date']!=''">
                <data field="start_date"><xsl:value-of select="col[@field='Start Date']"/></data>
            </xsl:if>
            <xsl:if test="$type!=0 or $type!=''">
                <!-- Will default to Staff if not defined -->
                <data field="type"><xsl:value-of select="$type"/></data>
            </xsl:if>
            <xsl:choose>
                <xsl:when test="$Status='obsolete'">
                    <data field="status">2</data>
                </xsl:when>
                <xsl:when test="$Status='retired'">
                    <data field="status">2</data>
                </xsl:when>
                <xsl:when test="$Status='resigned'">
                    <data field="status">2</data>
                </xsl:when>
                <xsl:when test="$Status='terminated'">
                    <data field="status">3</data>
                </xsl:when>
                <xsl:when test="$Status='died'">
                    <data field="status">4</data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Leave XML blank to default to 'Active' -->
                </xsl:otherwise>
            </xsl:choose>

            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>

            <!-- Link to Department -->
            <xsl:call-template name="Department">
                <xsl:with-param name="type">reference</xsl:with-param>
            </xsl:call-template>

            <!-- Link to Job Title -->
            <xsl:call-template name="JobTitle">
                <xsl:with-param name="type">reference</xsl:with-param>
            </xsl:call-template>

            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:call-template name="OrganisationID"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Office (staff only) -->
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
            <xsl:if test="$type=1 or $type=''">
                <reference field="site_id">
                    <xsl:attribute name="resource">
                        <xsl:value-of select="$resourcename"/>
                    </xsl:attribute>
                    <xsl:attribute name="tuid">
                        <xsl:call-template name="OrganisationID">
                            <xsl:with-param name="prefix">OFFICE:</xsl:with-param>
                            <xsl:with-param name="suffix" select="concat('/', $OfficeName)"/>
                        </xsl:call-template>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Mark as deployable -->
            <xsl:if test="$Deployable!=''">
                <xsl:choose>
                    <xsl:when test="$Deployable = 'true' or $Deployable = 'True'">
                        <resource name="deploy_application">
                            <data field="active" value="true"/>
                        </resource>
                    </xsl:when>
                    <xsl:when test="$Deployable = 'false' or $Deployable = 'False'">
                        <!-- No-op -->
                    </xsl:when>
                    <xsl:otherwise>
                        <resource name="deploy_application">
                            <data field="active" value="true"/>

                            <!-- Link to Organisation -->
                            <reference field="organisation_id" resource="org_organisation">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="concat('ORG:', $Deployable)"/>
                                </xsl:attribute>
                            </reference>

                        </resource>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>

            <!-- Deployments -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list" select="col[@field='Deployments']"/>
                <xsl:with-param name="arg">deployment</xsl:with-param>
            </xsl:call-template>

            <!-- Salary -->
            <xsl:if test="col[@field='Staff Level']/text() != '' or col[@field='Salary Grade']/text() != '' or col[@field='Monthly Salary']/text() != ''">
                <xsl:call-template name="Salary">
                    <xsl:with-param name="person_tuid">
                        <xsl:value-of select="$person_tuid"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <!-- Insurance -->
            <xsl:call-template name="Insurance"/>

            <!-- Contract Details -->
            <xsl:call-template name="Contract"/>

            <!-- Volunteer Details -->
            <xsl:variable name="VolDetailsActive" select="col[@field='Active']/text()"/>
            <xsl:variable name="VolDetailsType" select="col[@field='Volunteer Type']/text()"/>
            <xsl:if test="$VolDetailsActive='true' or $VolDetailsType!=''">
                <resource name="vol_details">
                    <xsl:if test="$VolDetailsActive='true'">
                        <data field="active" value="true"/>
                    </xsl:if>
                    <xsl:if test="$VolDetailsType!=''">
                        <data field="volunteer_type">
                            <xsl:choose>
                                <xsl:when test="$VolDetailsType='Governance Volunteer'">GOVERNANCE</xsl:when>
                                <xsl:when test="$VolDetailsType='Programme Volunteer'">PROGRAMME</xsl:when>
                            </xsl:choose>
                        </data>
                    </xsl:if>
                </resource>
            </xsl:if>

            <!-- Volunteer Cluster -->
            <xsl:if test="col[@field='Volunteer Cluster Type'] != '' or col[@field='Volunteer Cluster'] != '' or col[@field='Volunteer Cluster Position'] != ''">
              <resource name="vol_volunteer_cluster">
                <xsl:if test="col[@field='Volunteer Cluster Type'] != ''">
                    <reference field="vol_cluster_type_id" resource="vol_cluster_type">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='Volunteer Cluster Type']"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
                <xsl:if test="col[@field='Volunteer Cluster']!=''">
                    <reference field="vol_cluster_id" resource="vol_cluster">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat(col[@field='Volunteer Cluster Type'],col[@field='Volunteer Cluster'])"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
                <xsl:if test="col[@field='Volunteer Cluster Position'] != ''">
                    <reference field="vol_cluster_position_id" resource="vol_cluster_position">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='Volunteer Cluster Position']"/>
                        </xsl:attribute>
                    </reference>
                 </xsl:if>
               </resource>
            </xsl:if>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="IdentityInformation">
        <xsl:if test="col[@field='National ID']!=''">
            <resource name="pr_identity">
                <data field="type" value="2"/>
                <data field="value"><xsl:value-of select="col[@field='National ID']/text()"/></data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Passport No']!=''">
            <resource name="pr_identity">
                <data field="type" value="1"/>
                <data field="value"><xsl:value-of select="col[@field='Passport No']/text()"/></data>
                <data field="valid_until"><xsl:value-of select="col[@field='Passport Expiry Date']/text()"/></data>
                <xsl:variable name="l0" select="col[@field='Passport Country']/text()"/>
                <xsl:variable name="countrycode">
                    <xsl:choose>
                        <xsl:when test="string-length($l0)!=2">
                            <xsl:call-template name="countryname2iso">
                                <xsl:with-param name="country">
                                    <xsl:value-of select="$l0"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="uppercase">
                                <xsl:with-param name="string">
                                   <xsl:value-of select="$l0"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>

                <data field="country_code"><xsl:value-of select="$countrycode"/></data>

            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ContactInformation">

        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="col[@field='Email']"/></xsl:with-param>
            <xsl:with-param name="arg">email</xsl:with-param>
        </xsl:call-template>

        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="col[@field='Mobile Phone']"/></xsl:with-param>
            <xsl:with-param name="arg">mobile_phone</xsl:with-param>
        </xsl:call-template>

        <xsl:if test="col[@field='Home Phone']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="HOME_PHONE"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Home Phone']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Office Phone']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="WORK_PHONE"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Office Phone']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Skype']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="SKYPE"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Skype']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Callsign']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="RADIO"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Callsign']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Emergency Contact Name']!=''">
            <resource name="pr_contact_emergency">
                <data field="name">
                    <xsl:value-of select="col[@field='Emergency Contact Name']/text()"/>
                </data>
                <data field="relationship">
                    <xsl:value-of select="col[@field='Emergency Contact Relationship']/text()"/>
                </data>
                <data field="phone">
                    <xsl:value-of select="col[@field='Emergency Contact Phone']/text()"/>
                </data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Address">
        <xsl:param name="type"/>

        <resource name="pr_address">
            <!-- Link to Location -->
            <xsl:variable name="laddress_tuid" select="concat('Location Address:',
                                                              col[@field='First Name'],
                                                              col[@field='Middle Name'],
                                                              col[@field='Last Name'],
                                                              col[@field='Email'],
                                                              col[@field='Mobile Phone'],
                                                              $type
                                                              )"/>

            <reference field="location_id" resource="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$laddress_tuid"/>
                </xsl:attribute>
            </reference>

            <!-- Address Type -->
            <data field="type">
                <xsl:value-of select="$type"/>
            </data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Locations">
        <xsl:param name="type"/>
        <xsl:param name="address"/>
        <xsl:param name="postcode"/>
        <xsl:param name="l0"/>
        <xsl:param name="l1"/>
        <xsl:param name="l2"/>
        <xsl:param name="l3"/>
        <xsl:param name="l4"/>
        <xsl:param name="l5"/>
        <xsl:param name="lat"/>
        <xsl:param name="lon"/>

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('Location L4: ', $l4)"/>
        <xsl:variable name="l5id" select="concat('Location L5: ', $l5)"/>
        <xsl:variable name="laddress_tuid" select="concat('Location Address:',
                                                          col[@field='First Name'],
                                                          col[@field='Middle Name'],
                                                          col[@field='Last Name'],
                                                          col[@field='Email'],
                                                          col[@field='Mobile Phone'],
                                                          $type
                                                          )"/>

        <!-- Country Code = UUID of the L0 Location -->
        <xsl:variable name="countrycode">
            <xsl:choose>
                <xsl:when test="string-length($l0)!=2">
                    <xsl:call-template name="countryname2iso">
                        <xsl:with-param name="country">
                            <xsl:value-of select="$l0"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="uppercase">
                        <xsl:with-param name="string">
                           <xsl:value-of select="$l0"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

        <!-- L1 Location -->
        <xsl:if test="$l1!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l1id"/>
                </xsl:attribute>
                <reference field="parent" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
                <data field="name"><xsl:value-of select="$l1"/></data>
                <data field="level"><xsl:text>L1</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- L2 Location -->
        <xsl:if test="$l2!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l2id"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:otherwise>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:otherwise>
                </xsl:choose>
                <data field="name"><xsl:value-of select="$l2"/></data>
                <data field="level"><xsl:text>L2</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- L3 Location -->
        <xsl:if test="$l3!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l3id"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l2id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:otherwise>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:otherwise>
                </xsl:choose>
                <data field="name"><xsl:value-of select="$l3"/></data>
                <data field="level"><xsl:text>L3</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- L4 Location -->
        <xsl:if test="$l4!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l4id"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l3!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l3id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l2id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:otherwise>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:otherwise>
                </xsl:choose>
                <data field="name"><xsl:value-of select="$l4"/></data>
                <data field="level"><xsl:text>L4</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- L5 Location -->
        <xsl:if test="$l5!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l5id"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l4!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l4id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l3!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l3id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l2id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:otherwise>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:otherwise>
                </xsl:choose>
                <data field="name"><xsl:value-of select="$l4"/></data>
                <data field="level"><xsl:text>L4</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- Address Location -->
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$laddress_tuid"/>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="$l5!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l5id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l4!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l4id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l3!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l3id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l2!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l2id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l1!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$l1id"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:otherwise>
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$country"/>
                        </xsl:attribute>
                    </reference>
                </xsl:otherwise>
            </xsl:choose>
            <data field="name"><xsl:value-of select="$address"/></data>
            <data field="addr_street"><xsl:value-of select="$address"/></data>
            <data field="addr_postcode"><xsl:value-of select="$postcode"/></data>
            <data field="lat"><xsl:value-of select="$lat"/></data>
            <data field="lon"><xsl:value-of select="$lon"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="TR_ID_Locations">
        <xsl:param name="l1"/>
        <xsl:param name="l2"/>
        <xsl:param name="l3"/>

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>

        <!-- Country Code = UUID of the L0 Location -->
        <xsl:variable name="countrycode" select="TR"/>

        <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>

        <!-- L1 Location -->
        <xsl:if test="$l1!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l1id"/>
                </xsl:attribute>
                <reference field="parent" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
                <data field="name"><xsl:value-of select="$l1"/></data>
                <data field="level"><xsl:text>L1</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- L2 Location -->
        <xsl:if test="$l2!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l2id"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:otherwise>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:otherwise>
                </xsl:choose>
                <data field="name"><xsl:value-of select="$l2"/></data>
                <data field="level"><xsl:text>L2</xsl:text></data>
            </resource>
        </xsl:if>

        <!-- L3 Location -->
        <xsl:if test="$l3!=''">
            <resource name="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$l3id"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l2id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="$l1id"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:otherwise>
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="uuid">
                                <xsl:value-of select="$country"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:otherwise>
                </xsl:choose>
                <data field="name"><xsl:value-of select="$l3"/></data>
                <data field="level"><xsl:text>L3</xsl:text></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>
        <xsl:param name="arg2"/>
        <xsl:param name="org"/>
        <xsl:param name="date"/> <!-- Not accessible via SplitList currently -->

        <xsl:choose>
            <!-- Contacts -->
            <xsl:when test="$arg='email'">
                <resource name="pr_contact">
                    <data field="contact_method" value="EMAIL"/>
                    <data field="value"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>
            <xsl:when test="$arg='mobile_phone'">
                <resource name="pr_contact">
                    <data field="contact_method" value="SMS"/>
                    <data field="value"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>

            <!-- Deployable Roles -->
            <xsl:when test="$arg='deployablerole'">
                <resource name="hrm_job_title">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('DeployableRole:', $item)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$item"/></data>
                    <!-- Deployable -->
                    <data field="type">4</data>
                    <!-- No Organisation -->
                </resource>
            </xsl:when>
            <xsl:when test="$arg='deployablerole_ref'">
                <resource name="hrm_credential">
                    <reference field="job_title_id" resource="hrm_job_title">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('DeployableRole:', $item)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>

            <!-- Deployments -->
            <xsl:when test="$arg='deployment'">
                <resource name="deploy_assignment">
                    <reference field="mission_id" resource="deploy_mission">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Mission:', $item)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:when>

            <!-- Missions -->
            <xsl:when test="$arg='mission'">
                <resource name="deploy_mission">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Mission:', $item)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>

            <!-- Teams -->
            <xsl:when test="$arg='team'">
                <resource name="pr_group_membership">
                    <reference field="group_id" resource="pr_group">
                        <resource name="pr_group">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($TeamPrefix, $item)"/>
                            </xsl:attribute>
                            <data field="name"><xsl:value-of select="$item"/></data>
                            <!-- Relief Team -->
                            <data field="group_type">3</data>
                        </resource>
                    </reference>
                </resource>
            </xsl:when>

            <!-- Trainings -->
            <xsl:when test="$arg='training'">
                <resource name="hrm_training">
                    <reference field="course_id" resource="hrm_course">
                        <resource name="hrm_course">
                            <xsl:attribute name="tuid"><xsl:value-of select="$item"/></xsl:attribute>
                            <data field="name"><xsl:value-of select="$item"/></data>
                            <xsl:if test="not(starts-with($item, 'RDRT'))">
                                <!--
                                    Most training courses in Staff/Volunteer imports will be for that NS
                                    RDRT courses however should match the existing one linked to the IFRC Region
                                    @ToDo: Allow the org to be specified so that ones common to multiple regions can match the correct one
                                -->
                                <reference field="organisation_id" resource="org_organisation">
                                    <xsl:attribute name="tuid"><xsl:value-of select="concat('ORG:', $org)"/></xsl:attribute>
                                </reference>
                            </xsl:if>
                            <data field="external"><xsl:value-of select="$arg2"/></data>
                        </resource>
                    </reference>
                    <xsl:choose>
                        <xsl:when test="$date='' or $date='TRUE' or $date='True' or $date='true' or $date='YES' or $date='Yes' or $date='yes'">
                            <!-- no-op -->
                        </xsl:when>
                        <xsl:when test="contains($date, ';')">
                            <xsl:variable name="real_date">
                                <xsl:value-of select="substring-before($date, ';')"/>
                            </xsl:variable>
                            <xsl:variable name="venue">
                                <xsl:value-of select="substring-after($date, ';')"/>
                            </xsl:variable>
                            <data field="date"><xsl:value-of select="$real_date"/></data>
                            <reference field="training_event_id" resource="hrm_training_event">
                                <resource name="hrm_training_event">
                                    <reference field="course_id" resource="hrm_course">
                                        <xsl:attribute name="tuid"><xsl:value-of select="$item"/></xsl:attribute>
                                    </reference>
                                    <reference field="site_id" resource="org_facility">
                                        <resource name="org_facility">
                                            <data field="name"><xsl:value-of select="$venue"/></data>
                                        </resource>
                                    </reference>
                                    <data field="start_date"><xsl:value-of select="$real_date"/></data>
                                </resource>
                            </reference>
                        </xsl:when>
                        <xsl:otherwise>
                            <data field="date"><xsl:value-of select="$date"/></data>
                        </xsl:otherwise>
                    </xsl:choose>
                </resource>
            </xsl:when>

            <!-- Certificates -->
            <xsl:when test="$arg='certificate'">
                <resource name="hrm_certification">
                    <reference field="certificate_id" resource="hrm_certificate">
                        <resource name="hrm_certificate">
                            <xsl:attribute name="tuid"><xsl:value-of select="$item"/></xsl:attribute>
                            <data field="name"><xsl:value-of select="$item"/></data>
                        </resource>
                    </reference>
                    <xsl:if test="$date!='' and $date!='TRUE' and $date!='True' and $date!='true' and $date!='YES' and $date!='Yes' and $date!='yes'">
                        <data field="date"><xsl:value-of select="$date"/></data>
                    </xsl:if>
                </resource>
            </xsl:when>

        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="EducationLevel">
        <xsl:variable name="Level" select="col[@field='Education Level']"/>

        <xsl:if test="$Level!=''">
            <resource name="pr_education_level">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('EducationLevel:',$Level)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Level"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Education">

        <xsl:param name="level"/>
        <xsl:param name="name"/>
        <xsl:param name="major"/>
        <xsl:param name="grade"/>
        <xsl:param name="year"/>
        <xsl:param name="institute"/>

        <xsl:if test="$level!=''">
            <resource name="pr_education">
                <reference field="level_id" resource="pr_education_level">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('EducationLevel:',$level)"/>
                    </xsl:attribute>
                </reference>
                <data field="award">
                    <xsl:value-of select="$name"/>
                </data>
                <data field="major">
                    <xsl:value-of select="$major"/>
                </data>
                <data field="grade">
                    <xsl:value-of select="$grade"/>
                </data>
                <data field="year">
                    <xsl:value-of select="$year"/>
                </data>
                <data field="institute">
                    <xsl:value-of select="$institute"/>
                </data>
            </resource>
        </xsl:if>

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
    <xsl:template name="Slot">
        <xsl:variable name="SlotName" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$SlotName!=''">
            <resource name="pr_slot">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Slot:', $SlotName)"/>
                </xsl:attribute>
                <data field="name">
                    <xsl:value-of select="$SlotName"/>
                </data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Availability">
        <xsl:variable name="Options" select="col[@field='Availability']"/>
        <xsl:variable name="Comments" select="col[@field='Availability Comments']"/>

        <resource name="pr_person_availability">
            <xsl:if test="$Options!=''">
                <!-- @ToDo: A nicer way to handle options -->
                <data field="options">
                    <xsl:value-of select="col[@field='Availability']"/>
                </data>
            </xsl:if>
            <xsl:if test="$Comments!=''">
                <data field="comments">
                    <xsl:value-of select="col[@field='Availability Comments']"/>
                </data>
            </xsl:if>
            <xsl:for-each select="col[starts-with(@field, 'Slot')]">
                <xsl:call-template name="AvailabilitySlot" />
            </xsl:for-each>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="AvailabilitySlot">
        <xsl:variable name="Slot" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="text()"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
    
        <xsl:if test="$Value!=''">
            <resource name="pr_person_availability_slot">
                <xsl:if test="$Value='N' or $Value='NO' or $Value='F' or $Value='FALSE'">
                    <xsl:attribute name="deleted">
                        <xsl:text>true</xsl:text>
                    </xsl:attribute>
                </xsl:if>
                <reference field="slot_id" resource="pr_slot">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('Slot:', $Slot)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="DeployableOrg">
        <xsl:variable name="Deployable" select="col[@field='Deployable']"/>
        <xsl:if test="$Deployable!=''">
            <xsl:choose>
                <xsl:when test="$Deployable = 'true' or $Deployable = 'True'">
                    <!-- No-op -->
                </xsl:when>
                <xsl:when test="$Deployable = 'false' or $Deployable = 'False'">
                    <!-- No-op -->
                </xsl:when>
                <xsl:otherwise>
                    <resource name="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('ORG:', $Deployable)"/>
                        </xsl:attribute>
                        <data field="name"><xsl:value-of select="$Deployable"/></data>
                    </resource>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="VolunteerClusterType">
        <xsl:variable name="volunteerclustertype" select="col[@field='Volunteer Cluster Type']"/>
        <xsl:if test="$volunteerclustertype!=''">
            <resource name="vol_cluster_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$volunteerclustertype"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$volunteerclustertype"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="VolunteerCluster">
        <xsl:variable name="volunteercluster" select="col[@field='Volunteer Cluster']"/>
        <xsl:variable name="volunteerclustertype" select="col[@field='Volunteer Cluster Type']"/>
        <xsl:if test="$volunteercluster!=''">
            <resource name="vol_cluster">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($volunteerclustertype,$volunteercluster)"/>
                </xsl:attribute>
                <reference field="vol_cluster_type_id" resource="vol_cluster_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$volunteerclustertype"/>
                    </xsl:attribute>
                </reference>
                <data field="name"><xsl:value-of select="$volunteercluster"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="VolunteerClusterPosition">
        <xsl:variable name="volunteerclusterposition" select="col[@field='Volunteer Cluster Position']"/>
        <xsl:if test="$volunteerclusterposition!=''">
            <resource name="vol_cluster_position">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$volunteerclusterposition"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$volunteerclusterposition"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ******************************************************************
    <xsl:template name="Training">

        <xsl:param name="course"/>

        <xsl:if test="$course and $course!=''">
            <resource name="hrm_training">
                <reference field="course_id" resource="hrm_course">
                    <resource name="hrm_course">
                        <data field="name"><xsl:value-of select="$course"/></data>
                    </resource>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>
-->
    <!-- ******************************************************************
    <xsl:template name="Trainings">

        <xsl:param name="course_list"/>

        <xsl:if test="$course_list">
            <xsl:choose>
                <xsl:when test="contains($course_list, ',')">
                    <xsl:variable name="head" select="normalize-space(substring-before($course_list, ','))"/>
                    <xsl:variable name="tail" select="substring-after($course_list, ',')"/>
                    <xsl:call-template name="Training">
                        <xsl:with-param name="course" select="$head"/>
                    </xsl:call-template>
                    <xsl:call-template name="Trainings">
                        <xsl:with-param name="course_list" select="$tail"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="Training">
                        <xsl:with-param name="course" select="$course_list"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>

    </xsl:template>
-->
    <!-- ****************************************************************** -->
    <!-- Pull this in from training_event.xsl if-required
    <xsl:template name="Course">

        <xsl:variable name="CourseName" select="normalize-space(substring-after(@name, ':'))"/>
        <resource name="hrm_course">
            <xsl:attribute name="tuid"><xsl:value-of select="$CourseName"/></xsl:attribute>
            <data field="name"><xsl:value-of select="$CourseName"/></data>
        </resource>

    </xsl:template> -->

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
