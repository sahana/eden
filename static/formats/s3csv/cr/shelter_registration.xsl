<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Shelter Registrations - CSV Import Stylesheet

         Column headers defined in this stylesheet:

         Shelter........................required.....Shelter Name
         Unit...........................optional.....Shelter Unit Name
         Status.........................optional.....Shelter Registration Status
         Check-in Date..................optional.....Shelter Registration Check-In Date
         Check-out Date.................optional.....Shelter Registration Check-Out Date
         Reference......................optional.....Person pe_label
         First Name.....................required.....Person First Name
         Middle Name....................optional.....Person Middle Name
         Last Name......................optional.....Person Last Name
         DOB............................optional.....Person Date of Birth
         Nationality....................optional.....Person Nationality
         Email..........................optional.....person email address. Supports multiple comma-separated
         Mobile Phone...................optional.....person mobile phone number
         Home Address...................optional.....person home address
         Home Postcode..................optional.....person home address postcode
         Home Lat.......................optional.....person home address latitude
         Home Lon.......................optional.....person home address longitude
         Home Country...................optional.....person home address Country
         Home L1........................optional.....person home address L1
         Home L2........................optional.....person home address L2
         Home L3........................optional.....person home address L3
         Home L4........................optional.....person home address L4
         Comments.......................optional.....Shelter Registration Comments

         Column headers looked up in labels.xml:

         PersonGender...................optional.....person gender

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:param name="mode"/>

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
    <xsl:key name="shelter" match="row" use="col[@field='Shelter']"/>
    <xsl:key name="shelter_unit" match="row" use="col[@field='Unit']"/>

    <xsl:key name="person" match="row"
             use="concat(col[@field='First Name'], '/',
                         col[@field='Last Name'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <!-- Shelters -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('shelter', col[@field='Shelter'])[1])]">
                <xsl:call-template name="Shelter"/>
            </xsl:for-each>

            <!-- Shelter Units -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('shelter_unit', col[@field='Unit'])[1])]">
                <xsl:call-template name="ShelterUnit"/>
            </xsl:for-each>

            <!-- Persons -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('person',
                                                        concat(col[@field='First Name'], '/',
                                                               col[@field='Last Name']))[1])]">
                <xsl:call-template name="Person"/>
            </xsl:for-each>

            <!-- Process all table rows for shelter unit records -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Shelter Registration Record -->
    <xsl:template match="row">
        <xsl:variable name="ShelterName" select="col[@field='Shelter']/text()"/>
        <xsl:variable name="ShelterUnitName" select="col[@field='Unit']/text()"/>
        <xsl:variable name="Status">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Status']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="CheckInDate" select="col[@field='Check-in Date']/text()"/>
        <xsl:variable name="CheckOutDate" select="col[@field='Check-out Date']/text()"/>
        <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>

        <xsl:variable name="FirstName" select="col[@field='First Name']/text()"/>
        <xsl:variable name="MiddleName" select="col[@field='Middle Name']/text()"/>
        <xsl:variable name="LastName" select="col[@field='Last Name']/text()"/>

        <resource name="cr_shelter_registration">

            <reference field="shelter_id" resource="cr_shelter">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ShelterName"/>
                </xsl:attribute>
            </reference>

            <reference field="shelter_unit_id" resource="cr_shelter_unit">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($ShelterName,$ShelterUnitName)"/>
                </xsl:attribute>
            </reference>

            <reference field="person_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Person:', $LastName, ',', $MiddleName, ',', $FirstName)"/>
                </xsl:attribute>
            </reference>

            <data field="registration_status">
                <xsl:choose>
                    <xsl:when test="$Status='PLANNED'">
                        <xsl:text>1</xsl:text>
                    </xsl:when>
                    <xsl:when test="$Status='IN'">
                        <xsl:text>2</xsl:text>
                    </xsl:when>
                    <xsl:when test="$Status='OUT'">
                        <xsl:text>3</xsl:text>
                    </xsl:when>
                    <xsl:when test="$Status!=''">
                        <!-- Assume Numeric -->
                        <xsl:value-of select="$Status"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- Planned (legacy, left for backwards-compatibility) -->
                        <xsl:text>1</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </data>

            <xsl:if test="$CheckInDate!=''">
                <data field="check_in_date">
                    <xsl:value-of select="$CheckInDate"/>
                </data>
            </xsl:if>

            <xsl:if test="$CheckOutDate!=''">
                <data field="check_out_date">
                    <xsl:value-of select="$CheckOutDate"/>
                </data>
            </xsl:if>

            <xsl:if test="$Comments!=''">
                <data field="comments">
                    <xsl:value-of select="$Comments"/>
                </data>
            </xsl:if>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Shelter">
        <xsl:variable name="shelter" select="col[@field='Shelter']/text()"/>

        <resource name="cr_shelter">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$shelter"/>
            </xsl:attribute>

            <data field="name"><xsl:value-of select="$shelter"/></data>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="ShelterUnit">
        <xsl:variable name="ShelterName" select="col[@field='Shelter']/text()"/>
        <xsl:variable name="ShelterUnitName" select="col[@field='Unit']/text()"/>

        <xsl:if test="$ShelterName!='' and $ShelterUnitName!=''">
            <resource name="cr_shelter_unit">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($ShelterName,$ShelterUnitName)"/>
                </xsl:attribute>

                <data field="name">
                    <xsl:value-of select="$ShelterUnitName"/>
                </data>

                <reference field="shelter_id" resource="cr_shelter">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$ShelterName"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Person">
        <xsl:variable name="FirstName" select="col[@field='First Name']/text()"/>
        <xsl:variable name="MiddleName" select="col[@field='Middle Name']/text()"/>
        <xsl:variable name="LastName" select="col[@field='Last Name']/text()"/>
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
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Person:', $LastName, ',', $MiddleName, ',', $FirstName)"/>
            </xsl:attribute>
            <xsl:if test="col[@field='Reference']/text()!=''">
                <data field="pe_label"><xsl:value-of select="col[@field='Reference']/text()"/></data>
            </xsl:if>
            <data field="first_name"><xsl:value-of select="$FirstName"/></data>
            <data field="middle_name"><xsl:value-of select="$MiddleName"/></data>
            <data field="last_name"><xsl:value-of select="$LastName"/></data>
            <xsl:if test="col[@field='DOB']!=''">
                <data field="date_of_birth"><xsl:value-of select="col[@field='DOB']"/></data>
            </xsl:if>
            <xsl:if test="$gender!=''">
                <data field="gender">
                    <xsl:attribute name="value"><xsl:value-of select="$gender"/></xsl:attribute>
                </data>
            </xsl:if>
            <resource name="pr_person_details">
	            <xsl:variable name="l0">
                    <xsl:value-of select="col[@field='Nationality']"/>
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
            </resource>

            <!-- Contact Information -->
            <xsl:call-template name="ContactInformation"/>

            <!-- Addresses -->
            <xsl:if test="$home!='' or col[@field='Home Postcode']!='' or col[@field='Home L4']!='' or col[@field='Home L3']!='' or col[@field='Home L2']!='' or col[@field='Home L1']!=''">
                <xsl:call-template name="Address">
                    <xsl:with-param name="type">1</xsl:with-param>
                </xsl:call-template>
            </xsl:if>

            <!-- Arbitrary Tags -->
            <xsl:for-each select="col[starts-with(@field, 'KV')]">
                <xsl:call-template name="KeyValue"/>
            </xsl:for-each>

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

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="KeyValue">
        <xsl:variable name="Key" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$Value!=''">
            <!-- @ToDo
            <xsl:call-template name="splitList">
                <xsl:with-param name="list" select="$Value"/>
                <xsl:with-param name="arg">tag</xsl:with-param>
            </xsl:call-template> -->
            <resource name="pr_person_tag">
                <data field="tag"><xsl:value-of select="$Key"/></data>
                <data field="value"><xsl:value-of select="$Value"/></data>
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
</xsl:stylesheet>
