<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:org="http://eden.sahanafoundation.org/org">

    <!-- **********************************************************************
         Hospitals - CSV Import Stylesheet

         CSV fields:
         Name....................hms_hospital
         Code....................hms_hospital.code
         Type....................hms_hospital.facility_type
         Status..................hms_status.facility_status
         Reopening Date..........hms_status.date_reopening
         Power...................hms_status.power_supply_type
         Services................hms_services (Comma-separated List)
         Beds Total..............hms_hospital.total_beds
         Beds Available..........hms_hospital.available_beds
         Organisation............org_organisation
         Branch..................org_organisation[_branch]
         Country.................gis_location.L0 Name or ISO2
         Building................gis_location.name (Name used if not-provided)
         Address.................gis_location.addr_street
         Postcode................gis_location.addr_postcode
         L1......................gis_location.L1
         L2......................gis_location.L2
         L3......................gis_location.L3
         L4......................gis_location.L4
         Lat.....................gis_location.lat
         Lon.....................gis_location.lon
         Phone Switchboard.......hms_hospital
         Phone Business..........hms_hospital
         Phone Emergency.........hms_hospital
         Email...................hms_hospital
         Website.................hms_hospital
         Fax.....................hms_hospital
         Comments................hms_hospital
         KV:XXX..................org_site_tag Key/Value (Key = XX in column name, value = cell in row. Multiple allowed)

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>
    <xsl:include href="../../xml/countries.xsl"/>

    <xsl:variable name="LocationPrefix" select="'Location:'"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <!--<xsl:key name="hospital_type" match="row" use="col[@field='Type']"/>-->
    <xsl:key name="organisation" match="row" use="col[@field='Organisation']"/>
    <xsl:key name="branch" match="row"
             use="concat(col[@field='Organisation'], '/', col[@field='Branch'])"/>

    <!-- ****************************************************************** -->
    <!-- Lookup column names -->

    <xsl:variable name="Lat">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Lat</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="Lon">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Lon</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="Postcode">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">Postcode</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Hospital Types
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('hospital_type', col[@field='Type'])[1])]">
                <xsl:call-template name="HospitalType" />
            </xsl:for-each> -->

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

            <!-- Hospitals -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Create the variables -->
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="BranchName" select="col[@field='Branch']/text()"/>
        <xsl:variable name="HospitalName" select="col[@field='Name']/text()"/>

        <xsl:variable name="postcode">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Postcode"/>
            </xsl:call-template>
        </xsl:variable>

        <resource name="hms_hospital">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$HospitalName"/>
            </xsl:attribute>

            <!-- Link to Location -->
            <reference field="location_id" resource="gis_location">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($LocationPrefix, $HospitalName)"/>
                </xsl:attribute>
            </reference>

            <!-- Link to Organisation -->
            <xsl:if test="$OrgName!=''">
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
            </xsl:if>

            <!-- Arbitrary Tags -->
            <xsl:for-each select="col[starts-with(@field, 'KV')]">
                <xsl:call-template name="KeyValue"/>
            </xsl:for-each>

            <!-- Facility data -->
            <data field="name"><xsl:value-of select="$HospitalName"/></data>
            <data field="code"><xsl:value-of select="col[@field='Code']"/></data>

            <xsl:variable name="Address" select="col[@field='Address']/text()"/>
            <xsl:variable name="City" select="col[@field='L3']/text()"/>
            <xsl:if test="$Address!=''">
                <data field="address"><xsl:value-of select="$Address"/></data>
            </xsl:if>
            <xsl:if test="$postcode!=''">
                <data field="postcode"><xsl:value-of select="$postcode"/></data>
            </xsl:if>
            <xsl:if test="$City!=''">
                <data field="city"><xsl:value-of select="col[@field='L3']"/></data>
            </xsl:if>

            <xsl:variable name="PhoneSwitchboard" select="col[@field='Phone Switchboard']/text()"/>
            <xsl:variable name="PhoneBusiness" select="col[@field='Phone Business']/text()"/>
            <xsl:variable name="PhoneEmergency" select="col[@field='Phone Emergency']/text()"/>
            <xsl:if test="$PhoneSwitchboard!=''">
                <data field="phone_exchange"><xsl:value-of select="$PhoneSwitchboard"/></data>
            </xsl:if>
            <xsl:if test="$PhoneBusiness!=''">
                <data field="phone_business"><xsl:value-of select="$PhoneBusiness"/></data>
            </xsl:if>
            <xsl:if test="$PhoneEmergency!=''">
                <data field="phone_emergency"><xsl:value-of select="$PhoneEmergency"/></data>
            </xsl:if>

            <xsl:variable name="Email" select="col[@field='Email']/text()"/>
            <xsl:variable name="Website" select="col[@field='Website']/text()"/>
            <xsl:variable name="Fax" select="col[@field='Fax']/text()"/>
            <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>
            <xsl:if test="$Email!=''">
                <data field="email"><xsl:value-of select="$Email"/></data>
            </xsl:if>
            <xsl:if test="$Website!=''">
                <data field="website"><xsl:value-of select="$Website"/></data>
            </xsl:if>
            <xsl:if test="$Fax!=''">
                <data field="fax"><xsl:value-of select="$Fax"/></data>
            </xsl:if>
            <xsl:if test="$Comments!=''">
                <data field="comments"><xsl:value-of select="$Comments"/></data>
            </xsl:if>

            <!-- Hospital data -->
            <data field="total_beds"><xsl:value-of select="col[@field='Beds Total']"/></data>
            <data field="available_beds"><xsl:value-of select="col[@field='Beds Available']"/></data>

            <xsl:variable name="Type" select="col[@field='Type']/text()"/>
            <data field="facility_type">
                <xsl:choose>
                    <xsl:when test="$Type='Hospital'">1</xsl:when>
                    <xsl:when test="$Type='Field Hospital'">2</xsl:when>
                    <xsl:when test="$Type='Specialized Hospital'">3</xsl:when>
                    <xsl:when test="$Type='Health center'">11</xsl:when>
                    <xsl:when test="$Type='Health centre'">11</xsl:when>
                    <xsl:when test="$Type='Health center with beds'">12</xsl:when>
                    <xsl:when test="$Type='Health centre with beds'">12</xsl:when>
                    <xsl:when test="$Type='Health center without beds'">13</xsl:when>
                    <xsl:when test="$Type='Health centre without beds'">13</xsl:when>
                    <xsl:when test="$Type='Dispensary'">21</xsl:when>
                    <xsl:when test="$Type='Long-term care'">31</xsl:when>
                    <xsl:when test="$Type='ETC'">41</xsl:when>
                    <xsl:when test="$Type='Triage'">42</xsl:when>
                    <xsl:when test="$Type='Holding Center'">43</xsl:when>
                    <xsl:when test="$Type='Holding Centre'">43</xsl:when>
                    <xsl:when test="$Type='Transit Center'">44</xsl:when>
                    <xsl:when test="$Type='Transit Centre'">44</xsl:when>
                    <xsl:when test="$Type='Other'">98</xsl:when>
                    <xsl:otherwise>99</xsl:otherwise>
                </xsl:choose>
            </data>

            <xsl:variable name="Power" select="col[@field='Power']/text()"/>
            <xsl:variable name="Status" select="col[@field='Status']/text()"/>
            <xsl:variable name="ReopeningDate" select="col[@field='Reopening Date']/text()"/>
            <xsl:if test="$Status!='' or $ReopeningDate!='' or $Power!=''">
                <resource name="hms_status">
                    <xsl:if test="$Status!=''">
                        <data field="facility_status">
                            <xsl:choose>
                                <xsl:when test="$Status='Normal'">1</xsl:when>
                                <xsl:when test="$Status='Functional'">1</xsl:when>
                                <xsl:when test="$Status='Compromised'">2</xsl:when>
                                <xsl:when test="$Status='Evacuating'">3</xsl:when>
                                <xsl:when test="$Status='Closed'">4</xsl:when>
                                <xsl:when test="$Status='Pending'">5</xsl:when>
                            </xsl:choose>
                        </data>
                    </xsl:if>
                    <xsl:if test="$ReopeningDate!=''">
                        <data field="date_reopening"><xsl:value-of select="col[@field='Reopening Date']"/></data>
                    </xsl:if>
                    <xsl:if test="$Power!=''">
                        <data field="power_supply_type">
                            <xsl:choose>
                                <xsl:when test="$Power='Grid'">1</xsl:when>
                                <xsl:when test="$Power='Generator'">2</xsl:when>
                                <xsl:when test="$Power='Other'">98</xsl:when>
                                <xsl:when test="$Power='None'">99</xsl:when>
                            </xsl:choose>
                        </data>
                    </xsl:if>
                </resource>
            </xsl:if>

            <xsl:variable name="Services" select="col[@field='Services']/text()"/>
            <xsl:if test="$Services!=''">
                <resource name="hms_services">
                    <xsl:call-template name="Services">
                        <xsl:with-param name="list">
                            <xsl:value-of select="$Services"/>
                        </xsl:with-param>
                    </xsl:call-template>
                </resource>
            </xsl:if>

        </resource>

        <xsl:call-template name="Locations"/>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="KeyValue">
        <xsl:variable name="Key" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$Value!=''">
            <resource name="org_site_tag" alias="tag">
                <data field="tag"><xsl:value-of select="$Key"/></data>
                <data field="value"><xsl:value-of select="$Value"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Services">
        <xsl:param name="list"/>
        <xsl:variable name="listsep" select="','"/>

        <xsl:choose>
            <xsl:when test="contains($list, $listsep)">
                <xsl:variable name="Service" select="normalize-space(substring-before($list, $listsep))"/>
                <data field="$Service">True</data>
                <xsl:variable name="tail">
                    <xsl:value-of select="substring-after($list, $listsep)"/>
                </xsl:variable>
                <xsl:call-template name="Services">
                    <xsl:with-param name="list" select="$tail"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="normalize-space($list)!=''">
                    <xsl:variable name="Service" select="normalize-space($list)"/>
                    <data>
                        <xsl:attribute name="field">
                            <xsl:value-of select="$Service"/>
                        </xsl:attribute>
                        <xsl:text>1</xsl:text>
                    </data>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
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
    <xsl:template name="HospitalType">

        <xsl:variable name="Type" select="col[@field='Type']"/>

        <xsl:if test="$Type!=''">
            <resource name="hms_hospital_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('HospitalType:', $Type)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Type"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Locations">

        <xsl:variable name="HospitalName" select="col[@field='Name']/text()"/>
        <xsl:variable name="Building" select="col[@field='Building']/text()"/>
        <xsl:variable name="l0" select="col[@field='Country']/text()"/>
        <xsl:variable name="l1" select="col[@field='L1']/text()"/>
        <xsl:variable name="l2" select="col[@field='L2']/text()"/>
        <xsl:variable name="l3" select="col[@field='L3']/text()"/>
        <xsl:variable name="l4" select="col[@field='L4']/text()"/>
        <xsl:variable name="lat">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lat"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="lon">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Lon"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="postcode">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Postcode"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="AddressStreet" select="col[@field='Address']/text()"/>

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
                    <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
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
                    <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
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
                    <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
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
                    <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                </xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$l3!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l2!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                            </xsl:attribute>
                        </reference>
                    </xsl:when>
                    <xsl:when test="$l1!=''">
                        <reference field="parent" resource="gis_location">
                            <xsl:attribute name="tuid">
                                <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
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

        <!-- Hospital Location -->
        <resource name="gis_location">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($LocationPrefix, $HospitalName)"/>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="$l4!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L4/', $countrycode, '/', $l1, '/', $l2, '/', $l3, '/', $l4)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l3!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L3/', $countrycode, '/', $l1, '/', $l2, '/', $l3)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l2!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L2/', $countrycode, '/', $l1, '/', $l2)"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>
                <xsl:when test="$l1!=''">
                    <reference field="parent" resource="gis_location">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat('L1/', $countrycode, '/', $l1)"/>
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
            <xsl:choose>
                <xsl:when test="$Building!=''">
                    <data field="name"><xsl:value-of select="$Building"/></data>
                </xsl:when>
                <xsl:otherwise>
                    <data field="name"><xsl:value-of select="$HospitalName"/></data>
                </xsl:otherwise>
            </xsl:choose>

            <!-- Address -->
            <xsl:if test="$AddressStreet!=''">
                <data field="addr_street">
                    <xsl:value-of select="$AddressStreet"/>
                </data>
            </xsl:if>
            <xsl:if test="$postcode!=''">
                <data field="addr_postcode">
                    <xsl:value-of select="$postcode"/>
                </data>
            </xsl:if>

            <!-- Lat/Lon -->
            <xsl:if test="$lat!='' and $lon!=''">
                <data field="lat"><xsl:value-of select="$lat"/></data>
                <data field="lon"><xsl:value-of select="$lon"/></data>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
