<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Human Resources - CSV Import Stylesheet
         Must be imported through the pr_person resource

         Column headers defined in this stylesheet:

         Organisation...................required.....organisation name
         Branch.........................optional.....branch organisation name
         Type...........................optional.....HR type (staff|volunteer|member)
         Office.........................optional.....office name (required for staff)
         Office Lat.....................optional.....office latitude
         Office Lon.....................optional.....office longitude
         Office Street address..........optional.....office street address
         Office Country.................optional.....office country
         Office City....................optional.....office city
         Office Postcode................optional.....office postcode
         Job Title......................optional.....human_resource job title
         Job Role.......................optional.....human_resource job role
         Start Date.....................optional.....human_resource start date
         First Name.....................required.....person first name
         Middle Name....................optional.....person middle name
         Last Name......................optional.....person last name (required in some deployments)
         Initials.......................optional.....person initials
         DOB............................optional.....person date of birth
         Occupation.....................optional.....person_details occupation
         Company........................optional.....person_details company
         Affiliations............ ......optional.....person_details affiliation
         Father Name....................optional.....person_details father name
         Mother Name....................optional.....person_details mother name
         Religion.......................optional.....person_details religion
         Blood Type.....................optional.....pr_physical_description blood_type
         National ID....................optional.....person identity type = 2, value
         Passport No....................optional.....person identity type = 1, value
         Passport Country...............optional.....person identity
         Passport Expiry Date...........optional.....person identity
         Email..........................required.....person email address
         Mobile Phone...................optional.....person mobile phone number
         Home Phone.....................optional.....home phone number
         Office Phone...................optional.....office phone number
         Skype..........................optional.....person skype ID
         Callsign.......................optional.....person Radio Callsign
         Emergency Contact Name.........optional.....pr_contact_emergency name
         Emergency Contact Relationship.optional.....pr_contact_emergency relationship
         Emergency Contact Phone........optional.....pr_contact_emergency phone
         Home Address...................optional.....person home address
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
         Education Level................optional.....person education level of award (highest)
         Degree Name....................optional.....person education award
         Major..........................optional.....person education major
         Grade..........................optional.....person education grade
         Year...........................optional.....person education year
         Institute......................optional.....person education institute
         Volunteer Cluster Type.........optional.....volunteer_cluster cluster_type name
         Volunteer Cluster..............optional.....volunteer_cluster cluster name
         Volunteer Cluster Position.....optional.....volunteer_cluster cluster_position name

         Column headers looked up in labels.xml:

         PersonGender...................optional.....person gender
         JobTitle.......................optional.....HR Job Title/Volunteer Role/Position

         @ToDo:
            - add more labels.xml lookups
            - fix location hierarchy:
                - use country name in location_onaccept to match L0?
            - make updateable (don't use temporary UIDs)

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:variable name="TeamPrefix" select="'Team:'"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="PersonGender">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">PersonGender</xsl:with-param>
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

    <xsl:variable name="JobRole">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">JobRole</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="MemberType">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">MemberType</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="orgs"
             match="row"
             use="col[@field='Organisation']"/>

    <xsl:key name="branches" match="row"
             use="concat(col[@field='Organisation'], '/', col[@field='Branch'])"/>

    <xsl:key name="offices"
             match="row"
             use="concat(col[@field='Organisation'], '/', col[@field='Branch'], '/', col[@field='Office'])"/>

    <xsl:key name="jobtitles"
             match="row"
             use="col[contains($JobTitle, concat('|', @field, '|'))]"/>

    <xsl:key name="jobroles"
             match="row"
             use="col[contains($JobRole, concat('|', @field, '|'))]"/>
             
    <xsl:key name="volunteerclusters" 
             match="row"
             use="concat(col[@field='Volunteer Cluster Type'],
                         col[@field='Volunteer Cluster'])"/>

    <xsl:key name="volunteerclustertypes" 
             match="row"
             use="col[@field='Volunteer Cluster Type']"/>

    <xsl:key name="volunteerclustertpositions" 
             match="row"
             use="col[@field='Volunteer Cluster Position']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Top-level Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('orgs', col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName">
                        <xsl:value-of select="col[@field='Organisation']/text()"/>
                    </xsl:with-param>
                    <xsl:with-param name="BranchName"></xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Branches -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('branches', concat(col[@field='Organisation'], '/', col[@field='Branch']))[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName"></xsl:with-param>
                    <xsl:with-param name="BranchName">
                        <xsl:value-of select="col[@field='Branch']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Offices -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('offices',
                                                        concat(col[@field='Organisation'], '/',
                                                               col[@field='Branch'], '/',
                                                               col[@field='Office']))[1])]">
                <xsl:call-template name="Office"/>
            </xsl:for-each>

            <!-- Job Titles -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('jobtitles', col[contains($JobTitle, concat('|', @field, '|'))])[1])]">
                <xsl:call-template name="JobTitle">
                    <xsl:with-param name="type">resource</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Job Roles -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('jobroles', col[contains($JobRole, concat('|', @field, '|'))])[1])]">
                <xsl:call-template name="JobRole">
                    <xsl:with-param name="type">resource</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Volunteer Clusters -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('volunteerclusters', concat(col[@field='Volunteer Cluster Type'],col[@field='Volunteer Cluster']))[1])]">
                <xsl:call-template name="VolunteerCluster"/>
            </xsl:for-each>

            <!-- Volunteer Cluster Types -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('volunteerclustertypes', col[@field='Volunteer Cluster Type'])[1])]">
                <xsl:call-template name="VolunteerClusterType"/>
            </xsl:for-each>

            <!-- Volunteer Cluster Positions -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('volunteerclustertpositions', col[@field='Volunteer Cluster Position'])[1])]">
                <xsl:call-template name="VolunteerClusterPosition"/>
            </xsl:for-each>

            <!-- Process all table rows for person records -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>

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
                            <xsl:value-of select="$JobName"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:otherwise>
                    <resource name="hrm_job_title">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$JobName"/>
                        </xsl:attribute>

                        <data field="name">
                            <xsl:value-of select="$JobName"/>
                        </data>

                        <!-- Link to Organisation to filter lookup lists -->
                        <xsl:if test="$OrgName!=''">
                            <reference field="organisation_id" resource="org_organisation">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="$OrgName"/>
                                </xsl:attribute>
                            </reference>
                        </xsl:if>
                    </resource>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="JobRole">

        <xsl:param name="type"/>

        <xsl:variable name="JobName">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$JobRole"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <xsl:if test="$JobName!=''">
            <!-- Create the Job Role -->
            <xsl:choose>
                <xsl:when test="$type='reference'">
                    <reference field="job_role_id" resource="hrm_job_role">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$JobName"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:otherwise>
                    <resource name="hrm_job_role">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$JobName"/>
                        </xsl:attribute>

                        <data field="name">
                            <xsl:value-of select="$JobName"/>
                        </data>

                        <!-- Link to Organisation to filter lookup lists -->
                        <xsl:if test="$OrgName!=''">
                            <reference field="organisation_id" resource="org_organisation">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="$OrgName"/>
                                </xsl:attribute>
                            </reference>
                        </xsl:if>
                    </resource>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">
        <xsl:param name="OrgName"/>
        <xsl:param name="BranchName"/>

        <xsl:choose>
            <xsl:when test="$BranchName!=''">
                <!-- This is the Branch -->
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat(col[@field='Organisation'],$BranchName)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$BranchName"/></data>
                    <!-- Don't create Orgs as Branches of themselves -->
                    <xsl:if test="col[@field='Organisation']!=$BranchName">
                        <resource name="org_organisation_branch" alias="parent">
                            <reference field="organisation_id" resource="org_organisation">
                                <xsl:attribute name="tuid">
                                    <xsl:value-of select="col[@field='Organisation']"/>
                                </xsl:attribute>
                            </reference>
                        </resource>
                    </xsl:if>
                </resource>
            </xsl:when>
            <xsl:when test="$OrgName!=''">
                <!-- This is the top-level Organisation -->
                <resource name="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$OrgName"/></data>
                </resource>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Office">

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="BranchName" select="col[@field='Branch']/text()"/>
        <xsl:variable name="OfficeName" select="col[@field='Office']/text()"/>

        <xsl:if test="$OfficeName!=''">
            <resource name="org_office">

                <xsl:attribute name="tuid">
                    <xsl:value-of select="$OfficeName"/>
                </xsl:attribute>

                <data field="name"><xsl:value-of select="$OfficeName"/></data>

                <!-- Link to Organisation -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:choose>
                            <xsl:when test="$BranchName!=''">
                                <xsl:value-of select="concat($OrgName,$BranchName)"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="$OrgName"/>
                            </xsl:otherwise>
                        </xsl:choose>
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
                                        <xsl:value-of select="concat(
                                                                col[@field='Office Street address'], ', ',
                                                                col[@field='Office City'], ', ',
                                                                col[@field='Office Country'])"/>
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
        <xsl:variable name="BranchName" select="col[@field='Branch']/text()"/>
        <xsl:variable name="OfficeName" select="col[@field='Office']/text()"/>
        <xsl:variable name="Teams" select="col[@field='Teams']"/>

        <xsl:variable name="gender">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$PersonGender"/>
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

            <resource name="pr_person_details">
                <data field="father_name"><xsl:value-of select="col[@field='Father Name']"/></data>
                <data field="mother_name"><xsl:value-of select="col[@field='Mother Name']"/></data>
	            <xsl:if test="col[@field='Religion']">
	                <xsl:variable name="smallcase" select="'abcdefghijklmnopqrstuvwxyz'" />
	                <xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'" />
	                <xsl:variable name="religion">
	                    <xsl:value-of select="translate(col[@field='Religion'], $uppercase, $smallcase)"/>
	                </xsl:variable>
	                <data field="religion"><xsl:value-of select="$religion"/></data>
	            </xsl:if>
	            <data field="occupation"><xsl:value-of select="col[@field='Occupation']"/></data>
	            <data field="company"><xsl:value-of select="col[@field='Company']"/></data>
	            <data field="affiliations"><xsl:value-of select="col[@field='Affiliations']"/></data>
            </resource>

            <xsl:if test="col[@field='Blood Type']!=''">
                <resource name="pr_physical_description">
                    <data field="blood_type"><xsl:value-of select="col[@field='Blood Type']"/></data>
                </resource>
            </xsl:if>

            <!-- Identity Information -->
            <xsl:call-template name="IdentityInformation"/>

            <!-- Contact Information -->
            <xsl:call-template name="ContactInformation"/>

            <!-- Address -->
            <xsl:if test="col[@field='Home Address'] or col[@field='Home Postcode'] or col[@field='Home L4'] or col[@field='Home L3'] or col[@field='Home L2'] or col[@field='Home L1']">
                <xsl:call-template name="Address">
                    <xsl:with-param name="address" select="col[@field='Home Address']/text()"/>
                    <xsl:with-param name="postcode" select="col[@field='Home Postcode']/text()"/>
                    <xsl:with-param name="type">1</xsl:with-param>
                    <xsl:with-param name="l0" select="col[@field='Home Country']/text()"/>
                    <xsl:with-param name="l1" select="col[@field='Home L1']/text()"/>
                    <xsl:with-param name="l2" select="col[@field='Home L2']/text()"/>
                    <xsl:with-param name="l3" select="col[@field='Home L3']/text()"/>
                    <xsl:with-param name="l4" select="col[@field='Home L4']/text()"/>
                </xsl:call-template>
            </xsl:if>

            <xsl:if test="col[@field='Permanent Address'] or col[@field='Permanent Postcode'] or col[@field='Permanent L4'] or col[@field='Permanent L3'] or col[@field='Permanent L2'] or col[@field='Permanent L1']">
                <xsl:call-template name="Address">
                    <xsl:with-param name="address" select="col[@field='Permanent Address']/text()"/>
                    <xsl:with-param name="postcode" select="col[@field='Permanent Postcode']/text()"/>
                    <xsl:with-param name="type">2</xsl:with-param>
                    <xsl:with-param name="l0" select="col[@field='Permanent Country']/text()"/>
                    <xsl:with-param name="l1" select="col[@field='Permanent L1']/text()"/>
                    <xsl:with-param name="l2" select="col[@field='Permanent L2']/text()"/>
                    <xsl:with-param name="l3" select="col[@field='Permanent L3']/text()"/>
                    <xsl:with-param name="l4" select="col[@field='Permanent L4']/text()"/>
                </xsl:call-template>
            </xsl:if>

            <!-- HR record -->
            <xsl:choose>
                <xsl:when test="$type='3'">
                    <xsl:call-template name="Member">
                        <xsl:with-param name="OrgName" select="$OrgName"/>
                        <xsl:with-param name="BranchName" select="$BranchName"/>
                        <xsl:with-param name="type" select="$member"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="HumanResource">
                        <xsl:with-param name="OrgName" select="$OrgName"/>
                        <xsl:with-param name="BranchName" select="$BranchName"/>
                        <xsl:with-param name="OfficeName" select="$OfficeName"/>
                        <xsl:with-param name="type" select="$type"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>

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

            <!-- Trainings
            <xsl:call-template name="Trainings"/> -->

            <!-- Teams -->
            <xsl:call-template name="splitList">
                <xsl:with-param name="list"><xsl:value-of select="$Teams"/></xsl:with-param>
                <xsl:with-param name="arg">team</xsl:with-param>
            </xsl:call-template>

        </resource>

        <!-- Locations -->
        <xsl:if test="col[@field='Home Address'] or col[@field='Home Postcode'] or col[@field='Home L4'] or col[@field='Home L3'] or col[@field='Home L2'] or col[@field='Home L1']">
            <xsl:call-template name="Locations">
                <xsl:with-param name="address" select="col[@field='Home Address']/text()"/>
                <xsl:with-param name="postcode" select="col[@field='Home Postcode']/text()"/>
                <xsl:with-param name="type">1</xsl:with-param>
                <xsl:with-param name="l0" select="col[@field='Home Country']/text()"/>
                <xsl:with-param name="l1" select="col[@field='Home L1']/text()"/>
                <xsl:with-param name="l2" select="col[@field='Home L2']/text()"/>
                <xsl:with-param name="l3" select="col[@field='Home L3']/text()"/>
                <xsl:with-param name="l4" select="col[@field='Home L4']/text()"/>
                <xsl:with-param name="lat" select="col[@field='Home Lat']/text()"/>
                <xsl:with-param name="lon" select="col[@field='Home Lon']/text()"/>
            </xsl:call-template>
        </xsl:if>
        <xsl:if test="col[@field='Permanent Address'] or col[@field='Permanent Postcode'] or col[@field='Permanent L4'] or col[@field='Permanent L3'] or col[@field='Permanent L2'] or col[@field='Permanent L1']">
            <xsl:call-template name="Locations">
                <xsl:with-param name="address" select="col[@field='Permanent Address']/text()"/>
                <xsl:with-param name="postcode" select="col[@field='Permanent Postcode']/text()"/>
                <xsl:with-param name="type">2</xsl:with-param>
                <xsl:with-param name="l0" select="col[@field='Permanent Country']/text()"/>
                <xsl:with-param name="l1" select="col[@field='Permanent L1']/text()"/>
                <xsl:with-param name="l2" select="col[@field='Permanent L2']/text()"/>
                <xsl:with-param name="l3" select="col[@field='Permanent L3']/text()"/>
                <xsl:with-param name="l4" select="col[@field='Permanent L4']/text()"/>
                <xsl:with-param name="lat" select="col[@field='Permanent Lat']/text()"/>
                <xsl:with-param name="lon" select="col[@field='Permanent Lon']/text()"/>
            </xsl:call-template>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Member">

        <xsl:param name="OrgName"/>
        <xsl:param name="BranchName"/>
        <xsl:param name="type"/>

        <resource name="member_membership">

            <!-- Member data -->
            <data field="start_date"><xsl:value-of select="col[@field='Start Date']"/></data>
            <xsl:if test="$type!=0">
                <data field="type"><xsl:value-of select="$type"/></data>
            </xsl:if>

            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:choose>
                        <xsl:when test="$BranchName!=''">
                            <xsl:value-of select="concat($OrgName,$BranchName)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$OrgName"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </reference>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="HumanResource">

        <xsl:param name="OrgName"/>
        <xsl:param name="BranchName"/>
        <xsl:param name="OfficeName"/>
        <xsl:param name="type"/>

        <resource name="hrm_human_resource">

            <!-- HR data -->
            <data field="start_date"><xsl:value-of select="col[@field='Start Date']"/></data>
            <xsl:if test="$type!=0">
                <data field="type"><xsl:value-of select="$type"/></data>
            </xsl:if>

            <!-- Link to Job Role -->
            <xsl:call-template name="JobRole">
                <xsl:with-param name="type">reference</xsl:with-param>
            </xsl:call-template>

            <!-- Link to Job Title -->
            <xsl:call-template name="JobTitle">
                <xsl:with-param name="type">reference</xsl:with-param>
            </xsl:call-template>

            <!-- Link to Organisation -->
            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:choose>
                        <xsl:when test="$BranchName!=''">
                            <xsl:value-of select="concat($OrgName,$BranchName)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$OrgName"/>
                        </xsl:otherwise>
                    </xsl:choose>
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
            
            <!-- Volunteer Cluster (voluteers only) -->
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
                <xsl:variable name="passportCountry" select="col[@field='Passport Country']/text()"/>
                <xsl:variable name="countrycode">
                    <xsl:choose>
                        <xsl:when test="string-length($passportCountry)!=2">
                            <xsl:call-template name="countryname2iso">
                                <xsl:with-param name="country">
                                    <xsl:value-of select="$passportCountry"/>
                                </xsl:with-param>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="passportCountry"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>

                <data field="country_code"><xsl:value-of select="$countrycode"/></data>

            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ContactInformation">

        <xsl:if test="col[@field='Email']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="EMAIL"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Email']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Mobile Phone']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="SMS"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Mobile Phone']/text()"/>
                </data>
            </resource>
        </xsl:if>

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
        <xsl:param name="address"/>
        <xsl:param name="postcode"/>
        <xsl:param name="type"/>
        <xsl:param name="l0"/>
        <xsl:param name="l1"/>
        <xsl:param name="l2"/>
        <xsl:param name="l3"/>
        <xsl:param name="l4"/>

        <xsl:variable name="tuid" select="concat('pr_address/',
                                                 $address, '/',
                                                 $type, '/',
                                                 $l0, '/', $l1)"/>


        <resource name="pr_address">
            <!-- Link to Location -->
            <xsl:call-template name="LocationReference">
                <xsl:with-param name="address" select="$address"/>
                <xsl:with-param name="l0" select="$l0"/>
                <xsl:with-param name="l1" select="$l1"/>
                <xsl:with-param name="l2" select="$l2"/>
                <xsl:with-param name="l3" select="$l3"/>
                <xsl:with-param name="l4" select="$l4"/>
            </xsl:call-template>

            <!-- Address Type -->
            <data field="type">
                <xsl:value-of select="$type"/>
            </data>

            <!-- Populate the fields directly which are normally populated onvalidation -->
            <data field="building_name">
                <xsl:value-of select="$address"/>
            </data>
            <data field="address">
                <xsl:value-of select="$address"/>
            </data>
            <data field="postcode">
                <xsl:value-of select="$postcode"/>
            </data>
            <data field="L0">
                <xsl:value-of select="$l0"/>
            </data>
            <data field="L1">
                <xsl:value-of select="$l1"/>
            </data>
            <data field="L2">
                <xsl:value-of select="$l2"/>
            </data>
            <data field="L3">
                <xsl:value-of select="$l3"/>
            </data>
            <data field="L4">
                <xsl:value-of select="$l4"/>
            </data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="LocationReference">
        <xsl:param name="address"/>
        <xsl:param name="l0"/>
        <xsl:param name="l1"/>
        <xsl:param name="l2"/>
        <xsl:param name="l3"/>
        <xsl:param name="l4"/>

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('Location L4: ', $l4)"/>
        <xsl:variable name="l5id" select="concat('Location: ', $address)"/>

        <xsl:choose>
            <xsl:when test="$address!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l5id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l4!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l4id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l3!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l3id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l2!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l2id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l1!=''">
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$l1id"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
            <xsl:when test="$l0!=''">
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
                            <xsl:value-of select="$l0"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="country" select="concat('urn:iso:std:iso:3166:-1:code:', $countrycode)"/>
                <reference field="location_id" resource="gis_location">
                    <xsl:attribute name="uuid">
                        <xsl:value-of select="$country"/>
                    </xsl:attribute>
                </reference>
            </xsl:when>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Locations">
        <xsl:param name="address"/>
        <xsl:param name="postcode"/>
        <xsl:param name="l0"/>
        <xsl:param name="l1"/>
        <xsl:param name="l2"/>
        <xsl:param name="l3"/>
        <xsl:param name="l4"/>
        <xsl:param name="lat"/>
        <xsl:param name="lon"/>

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('Location L4: ', $l4)"/>
        <xsl:variable name="l5id" select="concat('Location: ', $address)"/>

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
                    <xsl:value-of select="$l0"/>
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

        <!-- Address Location -->
        <xsl:if test="$address!=''">
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
                <data field="name"><xsl:value-of select="$address"/></data>
                <data field="addr_street"><xsl:value-of select="$address"/></data>
                <data field="addr_postcode"><xsl:value-of select="$postcode"/></data>
                <data field="lat"><xsl:value-of select="$lat"/></data>
                <data field="lon"><xsl:value-of select="$lon"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>

        <xsl:choose>
            <!-- Team list -->
            <xsl:when test="$arg='team'">
                <resource name="pr_group_membership">
                    <reference field="group_id" resource="pr_group">
                        <resource name="pr_group">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat($TeamPrefix, $item)"/>
                            </xsl:attribute>
                            <data field="name"><xsl:value-of select="$item"/></data>
                            <!-- Relief Team -->
                            <data field="type">3</data>
                        </resource>
                    </reference>
                </resource>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Education">

        <xsl:param name="level"/>
        <xsl:param name="name"/>
        <xsl:param name="major"/>
        <xsl:param name="grade"/>
        <xsl:param name="year"/>
        <xsl:param name="institute"/>

        <xsl:if test="$name and $name!=''">
            <resource name="pr_education">
                <data field="level">
                    <xsl:value-of select="$level"/>
                </data>
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
