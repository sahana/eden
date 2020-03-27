<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Cases - CSV Import Stylesheet
         Must be imported through the pr_person resource

         Column headers defined in this stylesheet:

         Organisation...................required.....organisation name
         Branch.........................optional.....branch organisation name
         ...SubBranch,SubSubBranch...etc (indefinite depth, must specify all from root)

         Facility.......................optional.....Facility name
         Facility Type..................optional.....Office, Facility, Hospital, Shelter, Warehouse
         Case...........................optional.....dvr_case.reference
         Case Type......................optional.....dvr_case.case_type_id$name @ToDo
         Registration Date..............optional.....dvr_case.date
         Status.........................optional.....dvr_case.status_id$code
         Appointment:XX.................optional.....Appointment,Status (Type = XX in column name, Status = cell in row. Multiple allowed. Options: done, Date)

         Family.........................optional.....pr_group.name
         Head of Family.................optional.....pr_group_membership.group_head
                                                     true|false

         Shelter Unit...................optional.....cr_shelter_unit.name

         First Name.....................required.....person first name
         Middle Name....................optional.....person middle name
         Last Name......................optional.....person last name (required in some deployments)
         Label..........................optional.....pe_label
         Initials.......................optional.....person initials
         DOB............................optional.....person date of birth
         Year of Birth..................optional.....person_details year of birth
         Place of Birth.................optional.....person_details place of birth
         Marital Status.................optional.....person_details marital status
         Number of Children.............optional.....person_details number of children
         Nationality....................optional.....person_details nationality
                                                     (specify XX for "stateless")
         Occupation.....................optional.....person_details occupation
         Company........................optional.....person_details company
         Affiliations............ ......optional.....person_details affiliation
         Father Name....................optional.....person_details father name
         Mother Name....................optional.....person_details mother name
         Grandfather Name...............optional.....person_details grandfather name
         Grandmother Name...............optional.....person_details grandmother name
         Religion.......................optional.....person_details religion
         Religion other.................optional.....person_details religion_other
         Blood Type.....................optional.....pr_physical_description blood_type
         National ID....................optional.....person identity type = 2, value
         Passport No....................optional.....person identity type = 1, value
         Passport Country...............optional.....person identity
         Passport Expiry Date...........optional.....person identity
         Email..........................optional.....person email address. Supports multiple comma-separated
         Mobile Phone...................optional.....person mobile phone number
         Home Phone.....................optional.....home phone number
         Office Phone...................optional.....office phone number
         Skype..........................optional.....person skype ID
         Twitter........................optional.....person Twitter handle
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
         Education Level................optional.....person education level of award (highest)
         Degree Name....................optional.....person education award
         Major..........................optional.....person education major
         Grade..........................optional.....person education grade
         Year...........................optional.....person education year
         Institute......................optional.....person education institute
         Photo..........................optional.....pr_image.image (URL to remote server to download)

         Column headers looked up in labels.xml:

         PersonGender...................optional.....person gender

    *********************************************************************** -->
    <xsl:import href="../orgh.xsl"/>

    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="PersonGender">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">PersonGender</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="HomeAddress">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">HomeAddress</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="education_level" match="row"
             use="col[@field='Education Level']"/>

    <xsl:key name="family" match="row"
             use="col[@field='Family']"/>

    <xsl:key name="shelter_unit" match="row"
             use="col[@field='Shelter Unit']"/>

    <xsl:key name="status" match="row"
             use="col[@field='Status']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Import the organisation hierarchy -->
            <xsl:for-each select="table/row[1]">
                <xsl:call-template name="OrganisationHierarchy">
                    <xsl:with-param name="level">Organisation</xsl:with-param>
                    <xsl:with-param name="rows" select="//table/row"/>
                    <xsl:with-param name="FacilityColumn">Facility</xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Case Statuses -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('status',
                                                                   col[@field='Status'])[1])]">
                <xsl:call-template name="Status"/>
            </xsl:for-each>

            <!-- Case Appointment Types -->
            <xsl:for-each select="//row[1]/col[starts-with(@field, 'Appointment')]">
                <xsl:call-template name="AppointmentType"/>
            </xsl:for-each>

            <!-- Families -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('family',
                                                                   col[@field='Family'])[1])]">
                <xsl:call-template name="Family"/>
            </xsl:for-each>

            <!-- Shelter Units -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('shelter_unit',
                                                                   col[@field='Shelter Unit'])[1])]">
                <xsl:call-template name="ShelterUnit"/>
            </xsl:for-each>

            <!-- Education Levels -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('education_level',
                                                                   col[@field='Education Level'])[1])]">
                <xsl:call-template name="EducationLevel"/>
            </xsl:for-each>

            <!-- Process all table rows for person records -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Facility">

        <xsl:variable name="FacilityName" select="col[@field='Facility']/text()"/>
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
        <xsl:if test="$FacilityName!=''">
            <resource>
                <xsl:attribute name="name">
                    <xsl:value-of select="$resourcename"/>
                </xsl:attribute>
                <xsl:attribute name="tuid">
                    <xsl:call-template name="OrganisationID">
                        <xsl:with-param name="prefix">FACILITY:</xsl:with-param>
                        <xsl:with-param name="suffix" select="concat('/', $FacilityName)"/>
                    </xsl:call-template>
                </xsl:attribute>

                <data field="name"><xsl:value-of select="$FacilityName"/></data>

                <!-- Link to Organisation -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:call-template name="OrganisationID"/>
                    </xsl:attribute>
                </reference>

            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Person Record -->
    <xsl:template match="row">

        <xsl:variable name="FacilityName" select="col[@field='Facility']/text()"/>
        <xsl:variable name="FacilityType" select="col[@field='Facility Type']/text()"/>
        <xsl:variable name="Illiterate" select="col[@field='Illiterate']/text()"/>
        <xsl:variable name="MaritalStatus" select="col[@field='Marital Status']/text()"/>

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

        <resource name="pr_person">

            <!-- Case record -->
            <resource name="dvr_case">
                <xsl:if test="col[@field='Case']/text()!=''">
                    <data field="reference"><xsl:value-of select="col[@field='Case']/text()"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Registration Date']/text()!=''">
                    <data field="date"><xsl:value-of select="col[@field='Registration Date']/text()"/></data>
                </xsl:if>

                <xsl:if test="col[@field='Status']/text()!=''">
                    <reference field="status_id" resource="dvr_case_status">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Status:',col[@field='Status'])"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>

                <!-- Link to Organisation -->
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:call-template name="OrganisationID"/>
                    </xsl:attribute>
                </reference>

                <!-- Link to Site -->
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
                <xsl:if test="$FacilityName!=''">
                    <reference field="site_id">
                        <xsl:attribute name="resource">
                            <xsl:value-of select="$resourcename"/>
                        </xsl:attribute>
                        <xsl:attribute name="tuid">
                            <xsl:call-template name="OrganisationID">
                                <xsl:with-param name="prefix">FACILITY:</xsl:with-param>
                                <xsl:with-param name="suffix" select="concat('/', $FacilityName)"/>
                            </xsl:call-template>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
            </resource>

            <!-- Person record -->
            <data field="pe_label"><xsl:value-of select="col[@field='Label']/text()"/></data>
            <data field="first_name"><xsl:value-of select="col[@field='First Name']/text()"/></data>
            <xsl:if test="col[@field='Middle Name']/text()!=''">
                <data field="middle_name"><xsl:value-of select="col[@field='Middle Name']/text()"/></data>
            </xsl:if>
            <data field="last_name"><xsl:value-of select="col[@field='Last Name']/text()"/></data>
            <xsl:if test="col[@field='Initials']/text()!=''">
                <data field="initials"><xsl:value-of select="col[@field='Initials']/text()"/></data>
            </xsl:if>
            <xsl:if test="col[@field='DOB']/text()!=''">
                <data field="date_of_birth"><xsl:value-of select="col[@field='DOB']/text()"/></data>
            </xsl:if>
            <xsl:if test="$gender!=''">
                <data field="gender">
                    <xsl:attribute name="value"><xsl:value-of select="$gender"/></xsl:attribute>
                </data>
            </xsl:if>

            <!-- Appointments -->
            <xsl:for-each select="col[starts-with(@field, 'Appointment')]">
                <xsl:call-template name="Appointment"/>
            </xsl:for-each>

            <!-- Family -->
            <xsl:if test="col[@field='Family']/text()!=''">
                <resource name="pr_group_membership">
                    <xsl:if test="col[@field='Head of Family']/text()='true'">
                        <data field="group_head" value="true"/>
                    </xsl:if>
                    <reference field="group_id" resource="pr_group">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('Family:',col[@field='Family'])"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

            <!-- Shelter Registration -->
            <xsl:if test="col[@field='Shelter Unit']/text()!=''">
                <resource name="cr_shelter_registration">
                    <reference field="shelter_unit_id" resource="cr_shelter_unit">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('ShelterUnit:',col[@field='Shelter Unit'])"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

            <resource name="pr_person_details">
                <xsl:if test="$MaritalStatus!=''">
                    <data field="marital_status">
                            <xsl:choose>
                                <xsl:when test="$MaritalStatus='single'">
                                    <xsl:text>1</xsl:text>
                                </xsl:when>
                                <xsl:when test="$MaritalStatus='married'">
                                    <xsl:text>2</xsl:text>
                                </xsl:when>
                                <xsl:when test="$MaritalStatus='separated'">
                                    <xsl:text>3</xsl:text>
                                </xsl:when>
                                <xsl:when test="$MaritalStatus='divorced'">
                                    <xsl:text>4</xsl:text>
                                </xsl:when>
                                <xsl:when test="$MaritalStatus='widowed'">
                                    <xsl:text>5</xsl:text>
                                </xsl:when>
                                <xsl:otherwise>
                                    <!-- Unknown
                                    <xsl:value-of select="$MaritalStatus"/>-->
                                </xsl:otherwise>
                            </xsl:choose>
                    </data>
                </xsl:if>
                <xsl:if test="col[@field='Father Name']/text()!=''">
                    <data field="father_name"><xsl:value-of select="col[@field='Father Name']/text()"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Mother Name']/text()!=''">
                    <data field="mother_name"><xsl:value-of select="col[@field='Mother Name']/text()"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Grandfather Name']/text()!=''">
                    <data field="grandfather_name"><xsl:value-of select="col[@field='Grandfather Name']/text()"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Grandmother Name']/text()!=''">
                    <data field="grandmother_name"><xsl:value-of select="col[@field='Grandmother Name']/text()"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Number of Children']/text()!=''">
                    <data field="number_children"><xsl:value-of select="col[@field='Number of Children']/text()"/></data>
                </xsl:if>
                <xsl:if test="$Illiterate!=''">
                    <xsl:choose>
                        <xsl:when test="$Illiterate='Y'">
                            <data field="literacy">1</data>
                        </xsl:when>
                        <xsl:when test="$Illiterate='YES'">
                            <data field="literacy">1</data>
                        </xsl:when>
                        <xsl:when test="$Illiterate='T'">
                            <data field="literacy">1</data>
                        </xsl:when>
                        <xsl:when test="$Illiterate='TRUE'">
                            <data field="literacy">1</data>
                        </xsl:when>
                        <xsl:when test="$Illiterate='N'">
                            <data field="literacy">2</data>
                        </xsl:when>
                        <xsl:when test="$Illiterate='NO'">
                            <data field="literacy">2</data>
                        </xsl:when>
                        <xsl:when test="$Illiterate='F'">
                            <data field="literacy">2</data>
                        </xsl:when>
                        <xsl:when test="$Illiterate='FALSE'">
                            <data field="literacy">2</data>
                        </xsl:when>
                        <xsl:otherwise>
                            <!-- Unknown -->
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:if>
                <xsl:if test="col[@field='Religion']/text()!=''">
                    <data field="religion">
                        <xsl:call-template name="lowercase">
                            <xsl:with-param name="string">
                                <xsl:value-of select="col[@field='Religion']/text()"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </data>
                </xsl:if>
                <xsl:if test="col[@field='Religion other']/text()!=''">
                    <data field="religion_other"><xsl:value-of select="col[@field='Religion other']/text()"/></data>
                </xsl:if>

                <xsl:variable name="Nationality" select="col[@field='Nationality']/text()"/>
                <xsl:variable name="l0">
                    <xsl:choose>
                        <xsl:when test="$Nationality!='' and $Nationality!='XX'">
                            <!-- Stateless -->
                            <xsl:value-of select="$Nationality"/>
                        </xsl:when>
                        <xsl:when test="col[@field='Passport Country']/text()!=''">
                            <xsl:value-of select="col[@field='Passport Country']/text()"/>
                        </xsl:when>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="countrycode">
                    <xsl:choose>
                        <xsl:when test="$l0!='XX' and string-length($l0)!=2">
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

                <data field="nationality">
                    <xsl:choose>
                        <xsl:when test="$Nationality='XX'">
                            <xsl:value-of select="$Nationality"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$countrycode"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </data>

                <xsl:if test="col[@field='Place of Birth']/text()!=''">
                    <data field="place_of_birth"><xsl:value-of select="col[@field='Place of Birth']/text()"/></data>
                </xsl:if>

                <xsl:if test="col[@field='Year of Birth']/text()!=''">
                    <data field="year_of_birth"><xsl:value-of select="col[@field='Year of Birth']/text()"/></data>
                </xsl:if>

                <xsl:if test="col[@field='Occupation']/text()!=''">
                    <data field="occupation"><xsl:value-of select="col[@field='Occupation']/text()"/></data>
                </xsl:if>

                <xsl:if test="col[@field='Company']/text()!=''">
                    <data field="company"><xsl:value-of select="col[@field='Company']/text()"/></data>
                </xsl:if>

                <xsl:if test="col[@field='Affiliations']/text()!=''">
                    <data field="affiliations"><xsl:value-of select="col[@field='Affiliations']/text()"/></data>
                </xsl:if>
            </resource>

            <xsl:if test="col[@field='Blood Type']/text()!=''">
                <resource name="pr_physical_description">
                    <data field="blood_type"><xsl:value-of select="col[@field='Blood Type']/text()"/></data>
                </resource>
            </xsl:if>

            <!-- Identity Information -->
            <xsl:call-template name="IdentityInformation"/>

            <!-- Contact Information -->
            <xsl:call-template name="ContactInformation"/>

            <!-- Addresses -->
            <xsl:if test="$home!='' or col[@field='Home Postcode']/text()!='' or col[@field='Home L4']/text()!='' or col[@field='Home L3']/text()!='' or col[@field='Home L2']/text()!='' or col[@field='Home L1']/text()!=''">
                <xsl:call-template name="Address">
                    <xsl:with-param name="type">1</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <xsl:if test="col[@field='Permanent Address']/text()!='' or col[@field='Permanent Postcode']/text()!='' or col[@field='Permanent L4']/text()!='' or col[@field='Permanent L3']/text()!='' or col[@field='Permanent L2']/text()!='' or col[@field='Permanent L1']/text()!=''">
                <xsl:call-template name="Address">
                    <xsl:with-param name="type">2</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <!-- Education -->
            <xsl:call-template name="Education">
                <xsl:with-param name="level" select="col[@field='Education Level']/text()"/>
                <xsl:with-param name="name" select="col[@field='Degree Name']/text()"/>
                <xsl:with-param name="major" select="col[@field='Major']/text()"/>
                <xsl:with-param name="grade" select="col[@field='Grade']/text()"/>
                <xsl:with-param name="year" select="col[@field='Year']/text()"/>
                <xsl:with-param name="institute" select="col[@field='Institute']/text()"/>
            </xsl:call-template>

            <xsl:if test="col[@field='Photo']/text()!=''">
                <resource name="pr_image">
                    <!-- Set as Profile image -->
                    <data field="profile">true</data>
                    <!-- Photo -->
                    <data field="type">1</data>
                    <data field="image">
                        <xsl:attribute name="url">
                            <xsl:value-of select="col[@field='Photo']/text()"/>
                        </xsl:attribute>
                    </data>
                </resource>
            </xsl:if>

            <!-- Arbitrary Tags -->
            <xsl:for-each select="col[starts-with(@field, 'Tag')]">
                <xsl:call-template name="PersonTag"/>
            </xsl:for-each>

        </resource>

        <!-- Locations -->
        <xsl:if test="$home!='' or col[@field='Home Postcode']/text()!='' or col[@field='Home L4']/text()!='' or col[@field='Home L3']/text()!='' or col[@field='Home L2']/text()!='' or col[@field='Home L1']/text()!=''">
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
        <xsl:if test="col[@field='Permanent Address']/text()!='' or col[@field='Permanent Postcode']/text()!='' or col[@field='Permanent L4']/text()!='' or col[@field='Permanent L3']/text()!='' or col[@field='Permanent L2']/text()!='' or col[@field='Permanent L1']/text()!=''">
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
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="IdentityInformation">
        <xsl:if test="col[@field='National ID']/text()!=''">
            <resource name="pr_identity">
                <data field="type" value="2"/>
                <data field="value"><xsl:value-of select="col[@field='National ID']/text()"/></data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Passport No']/text()!=''">
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
            <xsl:with-param name="list"><xsl:value-of select="col[@field='Email']/text()"/></xsl:with-param>
            <xsl:with-param name="arg">email</xsl:with-param>
        </xsl:call-template>

        <xsl:if test="col[@field='Mobile Phone']/text()!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="SMS"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Mobile Phone']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Home Phone']/text()!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="HOME_PHONE"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Home Phone']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Office Phone']/text()!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="WORK_PHONE"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Office Phone']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Skype']/text()!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="SKYPE"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Skype']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Callsign']/text()!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="RADIO"/>
                <data field="value">
                    <xsl:value-of select="col[@field='Callsign']/text()"/>
                </data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Emergency Contact Name']/text()!=''">
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
                <data field="level"><xsl:text>L5</xsl:text></data>
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
    <xsl:template name="resource">
        <xsl:param name="item"/>
        <xsl:param name="arg"/>

        <xsl:choose>
            <xsl:when test="$arg='email'">
                <resource name="pr_contact">
                    <data field="contact_method" value="EMAIL"/>
                    <data field="value"><xsl:value-of select="$item"/></data>
                </resource>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="EducationLevel">
        <xsl:variable name="Level" select="col[@field='Education Level']/text()"/>

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
    <!-- Appointment Type, called in context of "Appointment:TypeName" columns -->
    <xsl:template name="AppointmentType">

        <xsl:variable name="TypeStr" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="AppointmentType">
            <xsl:choose>
                <xsl:when test="contains($TypeStr, ':')">
                    <xsl:value-of select="normalize-space(substring-after($TypeStr, ':'))"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$TypeStr"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <resource name="dvr_case_appointment_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('AppointmentType:', $AppointmentType)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$AppointmentType"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Appointment">
        <xsl:variable name="Key" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$Value!=''">
            <resource name="dvr_case_appointment">
                <reference field="type_id" resource="dvr_case_appointment_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('AppointmentType:',$Key)"/>
                    </xsl:attribute>
                </reference>
                <xsl:choose>
                    <xsl:when test="$Value='done'">
                        <data field="status">
                            <xsl:text>4</xsl:text>
                        </data>
                    </xsl:when>
                    <xsl:when test="$Value='missed'">
                        <data field="status">
                            <xsl:text>5</xsl:text>
                        </data>
                    </xsl:when>
                    <xsl:when test="$Value='cancelled'">
                        <!-- e.g. no X-Ray as pregnant -->
                        <data field="status">
                            <xsl:text>6</xsl:text>
                        </data>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- Assume a planned date -->
                        <data field="date">
                            <xsl:value-of select="$Value"/>
                        </data>
                        <data field="status">
                            <xsl:text>2</xsl:text>
                        </data>
                    </xsl:otherwise>
                </xsl:choose>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Family">
        <xsl:variable name="Family" select="col[@field='Family']/text()"/>

        <xsl:if test="$Family!=''">
            <resource name="pr_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Family:',$Family)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Family"/></data>
                <!-- Case -->
                <data field="group_type">7</data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ShelterUnit">
        <xsl:variable name="ShelterUnit" select="col[@field='Shelter Unit']/text()"/>

        <xsl:if test="$ShelterUnit!=''">
            <resource name="cr_shelter_unit">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('ShelterUnit:',$ShelterUnit)"/>
                </xsl:attribute>
                <!-- @ToDo: Add Shelter Name to aid uniqueness -->
                <data field="name"><xsl:value-of select="$ShelterUnit"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Status">
        <xsl:variable name="Status" select="col[@field='Status']/text()"/>

        <xsl:if test="$Status!=''">
            <resource name="dvr_case_status">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Status:',$Status)"/>
                </xsl:attribute>
                <data field="code"><xsl:value-of select="$Status"/></data>
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
    <xsl:template name="PersonTag">

        <xsl:variable name="Key" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$Value!=''">
            <resource name="pr_person_tag">
                <data field="tag"><xsl:value-of select="$Key"/></data>
                <data field="value"><xsl:value-of select="$Value"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- END ************************************************************** -->
</xsl:stylesheet>
