<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Person - CSV Import Stylesheet

         Column headers defined in this stylesheet:

         First Name.....................required.....person first name
         Middle Name....................optional.....person middle name
         Last Name......................optional.....person last name (required in some deployments)
         Initials.......................optional.....person initials
         DOB............................optional.....person date of birth
         Year of Birth..................optional.....person_details year of birth
         Place of Birth.................optional.....person_details place of birth
         Nationality....................optional.....person_details nationality
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
         Group Name.....................optional.....pr_group.name

         Column headers looked up in labels.xml:

         PersonGender...................optional.....person gender

    *********************************************************************** -->
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
    <xsl:key name="group_name" match="row"
             use="col[@field='Group Name']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Education Levels -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('education_level',
                                                                   col[@field='Education Level'])[1])]">
                <xsl:call-template name="EducationLevel"/>
            </xsl:for-each>

            <!-- Group Name -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('group_name',
                                                                   col[@field='Group Name'])[1])]">
                <xsl:call-template name="GroupInformation"/>
            </xsl:for-each>

            <!-- Process all table rows for person records -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Person Record -->
    <xsl:template match="row">

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

            <!-- Person record -->
            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
            <xsl:if test="col[@field='Middle Name']!=''">
                <data field="middle_name"><xsl:value-of select="col[@field='Middle Name']"/></data>
            </xsl:if>
            <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
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
                <xsl:if test="col[@field='Religion']!=''">
	                <data field="religion">
                        <xsl:call-template name="lowercase">
                            <xsl:with-param name="string">
                               <xsl:value-of select="col[@field='Religion']"/>
                            </xsl:with-param>
                        </xsl:call-template>
                    </data>
	            </xsl:if>
	            <xsl:if test="col[@field='Religion other']!=''">
	                <data field="religion_other"><xsl:value-of select="col[@field='Religion other']"/></data>
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
                <data field="nationality">
                    <xsl:value-of select="$countrycode"/>
                </data>
	            <xsl:if test="col[@field='Place of Birth']!=''">
                    <data field="place_of_birth"><xsl:value-of select="col[@field='Place of Birth']"/></data>
                </xsl:if>
                <xsl:if test="col[@field='Year of Birth']!=''">
                    <data field="year_of_birth"><xsl:value-of select="col[@field='Year of Birth']"/></data>
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

            <xsl:if test="col[@field='Blood Type']!=''">
                <resource name="pr_physical_description">
                    <data field="blood_type"><xsl:value-of select="col[@field='Blood Type']"/></data>
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

            <!-- Education -->
            <xsl:call-template name="Education">
                <xsl:with-param name="level" select="col[@field='Education Level']"/>
                <xsl:with-param name="name" select="col[@field='Degree Name']"/>
                <xsl:with-param name="major" select="col[@field='Major']"/>
                <xsl:with-param name="grade" select="col[@field='Grade']"/>
                <xsl:with-param name="year" select="col[@field='Year']"/>
                <xsl:with-param name="institute" select="col[@field='Institute']"/>
            </xsl:call-template>

            <xsl:if test="col[@field='Photo']!=''">
                <resource name="pr_image">
                    <!-- Set as Profile image -->
                    <data field="profile">true</data>
                    <!-- Photo -->
                    <data field="type">1</data>
                    <data field="image">
                        <xsl:attribute name="url">
                            <xsl:value-of select="col[@field='Photo']"/>
                        </xsl:attribute>
                    </data>
                </resource>
            </xsl:if>

            <!-- Link to Group -->
            <xsl:variable name="GroupName" select="col[@field='Group Name']/text()"/>
            <xsl:if test="$GroupName!=''">
                <resource name="pr_group_membership">
                    <reference field="group_id" resource="pr_group">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$GroupName"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>

        </resource>

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
    <xsl:template name="GroupInformation">
        <xsl:variable name="GroupName" select="col[@field='Group Name']/text()"/>
        <xsl:if test="$GroupName!=''">
            <resource name="pr_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$GroupName"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$GroupName"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ContactInformation">

        <xsl:call-template name="splitList">
            <xsl:with-param name="list"><xsl:value-of select="col[@field='Email']"/></xsl:with-param>
            <xsl:with-param name="arg">email</xsl:with-param>
        </xsl:call-template>

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

</xsl:stylesheet>
