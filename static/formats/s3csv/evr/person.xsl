<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Persons - CSV Import Stylesheet

         CSV column...........Format..........Content

         Organisation...............optional..........org_organisation.name
		 First Name.................required..........person first name
		 Middle Name................optional..........person middle name
         Last Name..................required..........person last name
         Person Gender..............required..........person gender
         DOB........................optional..........person date of birth
         Place of Birth.............optional..........person_details place of birth
         Fiscal Code................optional..........evr_case fiscal code
		 Home Address...............optional..........person home address
         Home Postcode..............optional..........person home address postcode
         Home Lat...................optional..........person home address latitude
         Home Lon...................optional..........person home address longitude
         Home L1....................optional..........person home address L1
         Home L2....................optional..........person home address L2
         Home L3....................optional..........person home address L3
         Home L4....................optional..........person home address L4
		 Home Phone.................optional..........person home phone number
		 Mobile Phone...............optional..........person mobile phone number
		 
    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->
	
	<xsl:variable name="Organisation">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Organisation</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>
	
    <xsl:variable name="PersonGender">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">PersonGender</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

	<!-- ****************************************************************** -->
	<!-- Indexes for faster processing -->
    <xsl:key name="organisation" match="row" use="col[@field='Organisation']"/>
	<xsl:key name="branch" match="row"
             use="concat(col[@field='Organisation'], '/', col[@field='Branch'])"/>
					
	
    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>

			<!-- Top-level Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation', col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName">
                        <xsl:value-of select="col[@field='Organisation']/text()"/>
                    </xsl:with-param>
                    <xsl:with-param name="BranchName"></xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>
			
			<!-- Branch Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('branch', concat(col[@field='Organisation'], '/',
                                                                                        col[@field='Branch']))[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="OrgName"></xsl:with-param>
                    <xsl:with-param name="BranchName">
                        <xsl:value-of select="col[@field='Branch']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>
			
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <xsl:template match="row">
		
		<!-- Create the variables -->
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="BranchName" select="col[@field='Branch']/text()"/>
		
        <xsl:variable name="gender">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$PersonGender"/>
            </xsl:call-template>
        </xsl:variable>
        
        <resource name="pr_person">
            <data field="last_name"><xsl:value-of select="col[@field='Last Name']"/></data>
            <data field="first_name"><xsl:value-of select="col[@field='First Name']"/></data>
			<data field="middle_name"><xsl:value-of select="col[@field='Middle Name']"/></data>
            <data field="date_of_birth"><xsl:value-of select="col[@field='Date of Birth']"/></data>
            <resource name="pr_person_details">
                <xsl:if test="col[@field='Place of Birth']!=''">
                    <data field="place_of_birth"><xsl:value-of select="col[@field='Place of Birth']"/></data>
                </xsl:if>
            </resource>
            <xsl:if test="$gender!=''">
                <data field="gender">
                    <xsl:attribute name="value"><xsl:value-of select="$gender"/></xsl:attribute>
                </data>
            </xsl:if>
			
			<!-- Contact Information -->
            <xsl:call-template name="ContactInformation"/>
			
			<!-- Address -->
            <xsl:call-template name="HomeAddress"/>
						
            <resource name="evr_case">
                <xsl:if test="col[@field='Fiscal Code']!=''">
                    <data field="fiscal_code"><xsl:value-of select="col[@field='Fiscal Code']"/></data>
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
        </resource>
		
		<!-- Locations -->
		<xsl:call-template name="Locations"/>
        
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
	<xsl:template name="ContactInformation">

        <xsl:if test="col[@field='Home Phone']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="HOME_PHONE"/>
                <data field="value"><xsl:value-of select="col[@field='Home Phone']/text()"/></data>
            </resource>
        </xsl:if>

        <xsl:if test="col[@field='Mobile Phone']!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="SMS"/>
                <data field="value"><xsl:value-of select="col[@field='Mobile Phone']/text()"/></data>
            </resource>
        </xsl:if>

    </xsl:template>
	
	<!-- ****************************************************************** -->
    <xsl:template name="HomeAddress">

        <xsl:if test="col[@field='Home Address'] or col[@field='Home Postcode'] or col[@field='Home L4'] or col[@field='Home L3'] or col[@field='Home L2'] or col[@field='Home L1']">
            <resource name="pr_address">
                <!-- Link to Location -->
                <xsl:call-template name="LocationReference"/>

                <!-- Home address -->
                <data field="type">1</data>

                <!-- Populate the fields directly which are normally populated onvalidation -->
                <data field="building_name"><xsl:value-of select="col[@field='Home Address']"/></data>
                <data field="address">
                    <xsl:value-of select="col[@field='Home Address']"/>
                </data>
                <data field="postcode">
                    <xsl:value-of select="col[@field='Home Postcode']"/>
                </data>
                <data field="L0">
                    <xsl:value-of select="col[@field='Home Country']"/>
                </data>
                <data field="L1">
                    <xsl:value-of select="col[@field='Home L1']"/>
                </data>
                <data field="L2">
                    <xsl:value-of select="col[@field='Home L2']"/>
                </data>
                <data field="L3">
                    <xsl:value-of select="col[@field='Home L3']"/>
                </data>
                <data field="L4">
                    <xsl:value-of select="col[@field='Home L4']"/>
                </data>
            </resource>
        </xsl:if>

    </xsl:template>
	
	<!-- ****************************************************************** -->
    <xsl:template name="LocationReference">

        <xsl:variable name="Address" select="col[@field='Home Address']/text()"/>

        <xsl:variable name="l0" select="col[@field='Home Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='Home L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='Home L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='Home L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='Home L4']/text()"/>

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('Location L4: ', $l4)"/>
        <xsl:variable name="l5id" select="concat('Location: ', $Address)"/>

        <xsl:choose>
            <xsl:when test="$Address!=''">
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
                            <xsl:call-template name="uppercase">
                                <xsl:with-param name="string">
                                   <xsl:value-of select="$l0"/>
                                </xsl:with-param>
                            </xsl:call-template>
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

        <xsl:variable name="Address" select="col[@field='Home Address']/text()"/>
        <xsl:variable name="l0" select="col[@field='Home Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='Home L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='Home L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='Home L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='Home L4']/text()"/>

        <xsl:variable name="l1id" select="concat('Location L1: ', $l1)"/>
        <xsl:variable name="l2id" select="concat('Location L2: ', $l2)"/>
        <xsl:variable name="l3id" select="concat('Location L3: ', $l3)"/>
        <xsl:variable name="l4id" select="concat('Location L4: ', $l4)"/>
        <xsl:variable name="l5id" select="concat('Location: ', $Address)"/>

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

        <!-- Address Location -->
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
            <data field="name"><xsl:value-of select="$Address"/></data>
            <data field="addr_street"><xsl:value-of select="$Address"/></data>
            <data field="addr_postcode"><xsl:value-of select="col[@field='Home Postcode']"/></data>
            <data field="lat"><xsl:value-of select="col[@field='Home Lat']"/></data>
            <data field="lon"><xsl:value-of select="col[@field='Home Lon']"/></data>
        </resource>

    </xsl:template>

</xsl:stylesheet>