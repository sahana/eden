<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
            xmlns:have="urn:oasis:names:tc:emergency:EDXL:HAVE:1.0"
            xmlns:gml="http://www.opengis.net/gml"
            xmlns:xnl="urn:oasis:names:tc:ciq:xnl:3"
            xmlns:xal="urn:oasis:names:tc:ciq:xal:3"
            xmlns:xpil="urn:oasis:names:tc:ciq:xpil:3">

    <!-- EDXL-HAVE Export Stylesheet

         Copyright (c) 2010-2012 Sahana Software Foundation

         Permission is hereby granted, free of charge, to any person
         obtaining a copy of this software and associated documentation
         files (the "Software"), to deal in the Software without
         restriction, including without limitation the rights to use,
         copy, modify, merge, publish, distribute, sublicense, and/or sell
         copies of the Software, and to permit persons to whom the
         Software is furnished to do so, subject to the following
         conditions:

         The above copyright notice and this permission notice shall be
         included in all copies or substantial portions of the Software.

         THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
         EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
         OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
         NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
         HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
         WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
         FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
         OTHER DEALINGS IN THE SOFTWARE.

    -->

    <!-- ****************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../xml/commons.xsl"/>
    <xsl:param name="domain"/>
    <xsl:param name="base_url"/>

    <!-- ****************************************************************** -->
    <!-- Root Element -->
    <xsl:template match="/">
        <xsl:apply-templates select="./s3xml"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Hospital Status -->
    <xsl:template match="s3xml">
        <have:HospitalStatus>
            <xsl:apply-templates select="./resource[@name='hms_hospital']"/>
        </have:HospitalStatus>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Hospital -->
    <xsl:template match="resource[@name='hms_hospital']">
        <xsl:if test="./data[@field='facility_type']/@value=1 or
                      ./data[@field='facility_type']/@value=2 or
                      ./data[@field='facility_type']/@value=3">

            <have:Hospital>

                <!-- Organization -->
                <have:Organization>
                    <xsl:call-template name="OrganizationInformation"/>
                    <xsl:call-template name="GeoLocation"/>
                </have:Organization>

                <!-- Services and Capacity -->
                <xsl:apply-templates select="./resource[@name='hms_status']"
                                     mode="EmergencyDeptStatus"/>
                <xsl:call-template name="BedCapacityStatus"/>
                <xsl:call-template name="ServiceCoverageStatus"/>

                <!-- Facility Status -->
                <have:HospitalFacilityStatus>
                    <xsl:apply-templates select="resource[@name='hms_status']"
                                         mode="FacilityStatus"/>
                    <xsl:call-template name="Activity24Hr"/>
                </have:HospitalFacilityStatus>

                <!-- Resources Status -->
                <xsl:call-template name="HospitalResourceStatus"/>

                <!-- Last Update Time -->
                <have:LastUpdateTime>
                    <xsl:value-of select="@modified_on"/>
                </have:LastUpdateTime>

            </have:Hospital>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Organization Information -->
    <xsl:template name="OrganizationInformation">
        <have:OrganizationInformation>
            <xsl:call-template name="OrganizationName"/>
            <xsl:call-template name="Addresses"/>
            <xsl:call-template name="ContactNumbers"/>
            <xsl:call-template name="ElectronicAddressIdentifiers"/>
        </have:OrganizationInformation>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- GeoLocation -->
    <xsl:template name="GeoLocation">
        <xsl:if test="./reference[@field='location_id']/@lat!='' and
                      ./reference[@field='location_id']/@lon!=''">
            <have:OrganizationGeoLocation>
                <gml:Point>
                    <xsl:attribute name="gml:id">
                        <xsl:choose>
                            <xsl:when test="starts-with(./reference[@field='location_id']/@uuid, 'urn:')">
                                <xsl:value-of select="./reference[@field='location_id']/@uuid"/>
                            </xsl:when>
                            <xsl:when test="contains(./reference[@field='location_id']/@uuid, '/')">
                                <xsl:value-of select="./reference[@field='location_id']/@uuid"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="concat(/s3xml/@domain, '/', ./reference[@field='location_id']/@uuid)"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                    <gml:coordinates>
                        <xsl:value-of select="./reference[@field='location_id']/@lat"/>
                        <xsl:text>, </xsl:text>
                        <xsl:value-of select="./reference[@field='location_id']/@lon"/>
                    </gml:coordinates>
                </gml:Point>
            </have:OrganizationGeoLocation>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Organization Name and ID -->
    <xsl:template name="OrganizationName">
        <xnl:OrganisationName>
            <xsl:attribute name="xnl:ID">
                <xsl:choose>
                    <xsl:when test="normalize-space(./data[@field='gov_uuid']/text())">
                        <xsl:value-of select="normalize-space(./data[@field='gov_uuid']/text())"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="./@uuid" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            <xnl:NameElement>
                <xsl:value-of select="./data[@field='name']/text()" />
            </xnl:NameElement>
        </xnl:OrganisationName>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Contact Numbers -->
    <xsl:template name="ContactNumbers">
        <xsl:variable name="phone_exchange" select="./data[@phone_exchange]"/>
        <xsl:variable name="phone_business" select="./data[@phone_business]"/>
        <xsl:variable name="phone_emergency" select="./data[@phone_emergency]"/>
        <xsl:variable name="fax" select="./data[@fax]"/>
        <xsl:if test="$phone_exchange/text()!='' or
                      $phone_business/text()!='' or
                      $phone_emergency/text()!='' or
                      $fax/text()!=''">
            <xpil:ContactNumbers>
                <xsl:if test="$phone_exchange/text()!=''">
                    <xpil:ContactNumber xpil:MediaType="Telephone" xpil:ContactNature="Exchange">
                        <xpil:ContactNumberElement>
                            <xsl:value-of select="$phone_exchange/text()" />
                        </xpil:ContactNumberElement>
                    </xpil:ContactNumber>
                </xsl:if>
                <xsl:if test="$phone_business/text()!=''">
                    <xpil:ContactNumber xpil:MediaType="Telephone" xpil:ContactNature="Business">
                        <xpil:ContactNumberElement>
                            <xsl:value-of select="$phone_business/text()" />
                        </xpil:ContactNumberElement>
                    </xpil:ContactNumber>
                </xsl:if>
                <xsl:if test="$phone_emergency/text()!=''">
                    <xpil:ContactNumber xpil:MediaType="Telephone" xpil:ContactNature="Emergency">
                        <xpil:ContactNumberElement>
                            <xsl:value-of select="$phone_emergency/text()" />
                        </xpil:ContactNumberElement>
                    </xpil:ContactNumber>
                </xsl:if>
                <xsl:if test="$fax/text()!=''">
                    <xpil:ContactNumber xpil:MediaType="Fax">
                        <xpil:ContactNumberElement>
                            <xsl:value-of select="$fax/text()" />
                        </xpil:ContactNumberElement>
                    </xpil:ContactNumber>
                </xsl:if>
            </xpil:ContactNumbers>
        </xsl:if>
      </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Electronic Address Identifiers -->
    <xsl:template name="ElectronicAddressIdentifiers">
        <xsl:variable name="email" select="./data[@field='email']"/>
        <xsl:variable name="website" select="./data[@field='website']"/>
        <xsl:if test="$email/text()!='' or $website/text()!=''">
            <xpil:ElectronicAddressIdentifiers>
                <xsl:if test="$email/text()!=''">
                    <xpil:ElectronicAddressIdentifier xpil:Type="EMAIL">
                        <xsl:value-of select="$email/text()"/>
                    </xpil:ElectronicAddressIdentifier>
                </xsl:if>
                <xsl:if test="$website/text()!=''">
                    <xpil:ElectronicAddressIdentifier xpil:Type="URL">
                        <xsl:value-of select="$website/text()"/>
                    </xpil:ElectronicAddressIdentifier>
                </xsl:if>
            </xpil:ElectronicAddressIdentifiers>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Addresses -->
    <xsl:template name="Addresses">
        <xsl:variable name="address" select="./data[@field='address']"/>
        <xsl:variable name="city" select="./data[@field='city']"/>
        <xsl:variable name="postcode" select="./data[@field='postcode']"/>
        <xsl:if test="$city/text()!=''">
            <xpil:Addresses>
                <xal:Address>
                    <xsl:if test="$address/text()!=''">
                        <xal:FreeTextAddress>
                            <xal:AddressLine>
                                <xsl:value-of select="$address/text()"/>
                            </xal:AddressLine>
                        </xal:FreeTextAddress>
                    </xsl:if>
                    <xal:Locality xal:Type="town">
                        <xal:NameElement xal:NameType="Name">
                            <xsl:value-of select="$city/text()"/>
                        </xal:NameElement>
                    </xal:Locality>
                    <xsl:if test="$postcode/text()!=''">
                        <xal:PostCode>
                            <xal:Identifier>
                                <xsl:value-of select="$postcode/text()"/>
                            </xal:Identifier>
                        </xal:PostCode>
                    </xsl:if>
                </xal:Address>
            </xpil:Addresses>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Bed Capacity -->
    <!-- @todo: export broken down by bed type -->
    <xsl:template name="BedCapacityStatus">
        <have:HospitalBedCapacityStatus>
            <xsl:for-each select="./resource[@name='hms_bed_capacity']">
                <have:BedCapacity>
                    <have:BedType>
                        <xsl:choose>
                            <xsl:when test="./data[@field='bed_type']/@value='1'">AdultICU</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='2'">PediatricICU</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='3'">NeonatalICU</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='4'">EmergencyDepartment</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='5'">NurseryBeds</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='6'">MedicalSurgical</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='7'">RehabLongTermCare</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='8'">Burn</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='9'">Pediatrics</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='10'">AdultPsychiatric</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='11'">PediatricPsychiatric</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='12'">NegativeFlowIsolation</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='13'">OtherIsolation</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='14'">OperatingRooms</xsl:when>
                            <xsl:when test="./data[@field='bed_type']/@value='15'">CholeraTreatment</xsl:when>
                            <xsl:otherwise>Other</xsl:otherwise>
                        </xsl:choose>
                    </have:BedType>
                    <have:CapacityStatus>VacantAvailable</have:CapacityStatus>
                    <have:AvailableCount>
                        <xsl:value-of select="./data[@field='beds_available']/text()" />
                    </have:AvailableCount>
                    <have:BaselineCount>
                        <xsl:value-of select="./data[@field='beds_baseline']/text()" />
                    </have:BaselineCount>
                </have:BedCapacity>
            </xsl:for-each>
        </have:HospitalBedCapacityStatus>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Service Coverage -->
    <xsl:template name="ServiceCoverageStatus">
        <xsl:apply-templates select="./resource[@name='hms_services']"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Activites 24hrs -->
    <!-- @todo: check for modification date - current? -->
    <xsl:template name="Activity24Hr">
        <xsl:for-each select="./resource[@name='hms_activity']">
            <xsl:sort select="./data[@field='date']" order="descending"/>
            <xsl:if test="position()=1">
                <have:Activity24Hr>
                    <have:Admissions>
                        <xsl:value-of select="./data[@field='admissions24']"/>
                    </have:Admissions>
                    <have:Discharges>
                        <xsl:value-of select="./data[@field='discharges24']"/>
                    </have:Discharges>
                    <have:Deaths>
                        <xsl:value-of select="./data[@field='deaths24']"/>
                    </have:Deaths>
                </have:Activity24Hr>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>


    <!-- ****************************************************************** -->
    <!-- Resource Information -->
    <xsl:template name="HospitalResourceStatus">
        <have:HospitalResourceStatus>
            <xsl:apply-templates select="resource[@name='hms_status']"
                                 mode="FacilityOperations"/>

            <xsl:if test="./data[@field='doctors']/text()">
                <have:ResourceInformationText>
                    <xsl:text>Doctors: </xsl:text>
                    <xsl:value-of select="./data[@field='doctors']/text()"/>
                </have:ResourceInformationText>
            </xsl:if>

            <xsl:if test="./data[@field='nurses']/text()">
                <have:ResourceInformationText>
                    <xsl:text>Nurses: </xsl:text>
                    <xsl:value-of select="./data[@field='nurses']/text()"/>
                </have:ResourceInformationText>
            </xsl:if>

            <xsl:if test="./data[@field='non_medical_staff']/text()">
                <have:ResourceInformationText>
                    <xsl:text>Non-medical staff: </xsl:text>
                    <xsl:value-of select="./data[@field='non_medical_staff']/text()"/>
                </have:ResourceInformationText>
            </xsl:if>

            <!--
            <xsl:if test="./resource[@name='hms_ctc_capability']/data[@field='ctc']/@value='True'">
                <have:ResourceInformationText>
                    <xsl:text>CTC Information: </xsl:text>
                </have:ResourceInformationText>
            </xsl:if>
            -->

            <xsl:apply-templates select="./resource[@name='hms_shortage']"/>
        </have:HospitalResourceStatus>
    </xsl:template>


    <!-- ****************************************************************** -->
    <!-- Status reports -->

    <!-- Helper for Resource Status Options -->
    <xsl:template name="ResourceStatusOptions">
        <xsl:param name="value"/>
        <xsl:choose>
            <xsl:when test="$value='2'">
                <xsl:text>Insufficient</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>Adequate</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- Emergency Department Status -->

    <xsl:template match="resource[@name='hms_status']" mode="EmergencyDeptStatus">
        <have:EmergencyDepartmentStatus>
            <have:EMSTraffic>
                <have:EMSTrafficStatus>
                    <xsl:choose>
                        <xsl:when test="./data[@field='ems_status']/@value='1'">
                            <xsl:text>Normal</xsl:text>
                        </xsl:when>
                        <xsl:when test="./data[@field='ems_status']/@value='2'">
                            <xsl:text>Advisory</xsl:text>
                        </xsl:when>
                        <xsl:when test="./data[@field='ems_status']/@value='3'">
                            <xsl:text>Closed</xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>Unknown</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </have:EMSTrafficStatus>
                <xsl:if test="./data[@field='ems_reason']/text()!=''">
                    <have:EMSTrafficReason>
                        <xsl:value-of select="./data[@field='ems_reason']/text()"/>
                    </have:EMSTrafficReason>
                </xsl:if>
            </have:EMSTraffic>
        </have:EmergencyDepartmentStatus>
    </xsl:template>

    <!-- Facility Status -->

    <xsl:template match="resource[@name='hms_status']" mode="FacilityStatus">
        <have:FacilityStatus>
            <xsl:choose>
                <xsl:when test="./data[@field='facility_status']/@value='1'">
                    <xsl:text>Normal</xsl:text>
                </xsl:when>
                <xsl:when test="./data[@field='facility_status']/@value='2'">
                    <xsl:text>Compromised</xsl:text>
                </xsl:when>
                <xsl:when test="./data[@field='facility_status']/@value='3'">
                    <xsl:text>Evacuating</xsl:text>
                </xsl:when>
                <xsl:when test="./data[@field='facility_status']/@value='4'">
                    <xsl:text>Closed</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>Unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </have:FacilityStatus>

        <have:ClinicalStatus>
            <xsl:choose>
                <xsl:when test="./data[@field='clinical_status']/@value='1'">
                    <xsl:text>Normal</xsl:text>
                </xsl:when>
                <xsl:when test="./data[@field='clinical_status']/@value='2'">
                    <xsl:text>Full</xsl:text>
                </xsl:when>
                <xsl:when test="./data[@field='clinical_status']/@value='3'">
                    <xsl:text>Closed</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>NotApplicable</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </have:ClinicalStatus>

        <xsl:if test="./data[@field='morgue_status']/@value or
                      ./data[@field='morgue_units']/text()!=''">
            <have:MorgueCapacity>
                <xsl:if test="./data[@field='morgue_status']/@value">
                    <have:MorgueCapacityStatus>
                        <xsl:choose>
                            <xsl:when test="./data[@field='morgue_status']/@value='1'">
                                <xsl:text>Open</xsl:text>
                            </xsl:when>
                            <xsl:when test="./data[@field='morgue_status']/@value='2'">
                                <xsl:text>Full</xsl:text>
                            </xsl:when>
                            <xsl:when test="./data[@field='morgue_status']/@value='3'">
                                <xsl:text>Exceeded</xsl:text>
                            </xsl:when>
                            <xsl:when test="./data[@field='morgue_status']/@value='4'">
                                <xsl:text>Closed</xsl:text>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:text>Unknown</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </have:MorgueCapacityStatus>
                </xsl:if>
                <xsl:if test="./data[@field='morgue_units']/text()!=''">
                    <have:MorgueCapacityUnits>
                        <xsl:value-of select="./data[@field='morgue_units']/text()"/>
                    </have:MorgueCapacityUnits>
                </xsl:if>
            </have:MorgueCapacity>
        </xsl:if>

        <have:SecurityStatus>
            <xsl:choose>
                <xsl:when test="./data[@field='security_status']/@value='1'">
                    <xsl:text>Normal</xsl:text>
                </xsl:when>
                <xsl:when test="./data[@field='security_status']/@value='2'">
                    <xsl:text>Elevated</xsl:text>
                </xsl:when>
                <xsl:when test="./data[@field='security_status']/@value='3'">
                    <xsl:text>RestrictedAccess</xsl:text>
                </xsl:when>
                <xsl:when test="./data[@field='security_status']/@value='4'">
                    <xsl:text>Lockdown</xsl:text>
                </xsl:when>
                <xsl:when test="./data[@field='security_status']/@value='5'">
                    <xsl:text>Quarantine</xsl:text>
                </xsl:when>
                <xsl:when test="./data[@field='security_status']/@value='6'">
                    <xsl:text>Closed</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>Unknown</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </have:SecurityStatus>
    </xsl:template>

    <!-- Facility operations -->

    <xsl:template match="resource[@name='hms_status']" mode="FacilityOperations">
        <have:FacilityOperations>
            <xsl:call-template name="ResourceStatusOptions">
                <xsl:with-param name="value" select="./data[@field='facility_operations']/@value"/>
            </xsl:call-template>
        </have:FacilityOperations>
        <have:ClinicalOperations>
            <xsl:call-template name="ResourceStatusOptions">
                <xsl:with-param name="value" select="./data[@field='clinical_operations']/@value"/>
            </xsl:call-template>
        </have:ClinicalOperations>
        <have:Staffing>
            <xsl:call-template name="ResourceStatusOptions">
                <xsl:with-param name="value" select="./data[@field='staffing']/@value"/>
            </xsl:call-template>
        </have:Staffing>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Helper for Comments -->
    <xsl:template match="resource[@name='hms_shortage']">
        <xsl:if test="./data[@field='status']/@value='1' or ./data[@field='status']/@value='2'">
            <have:CommentText>
                <xsl:text>[Priority: </xsl:text>
                <xsl:value-of select="./data[@field='priority']/text()"/>
                <xsl:text>] </xsl:text>
                <xsl:text>Shortage (</xsl:text>
                <xsl:value-of select="./data[@field='type']/text()"/>
                <xsl:text>/</xsl:text>
                <xsl:value-of select="./data[@field='impact']/text()"/>
                <xsl:text>): </xsl:text>
                <xsl:value-of select="./data[@field='description']/text()"/>
            </have:CommentText>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Service Coverage Status -->
    <xsl:template match="resource[@name='hms_services']">
        <have:ServiceCoverageStatus>
            <xsl:if test="starts-with(./data[@field='tran']/text(), 'T') or
                          starts-with(./data[@field='tair']/text(), 'T')">
                <have:TransportServicesIndicator>
                    <have:TransportServicesSubType>
                        <xsl:if test="starts-with(./data[@field='tran']/text(), 'T')">
                            <have:AmbulanceServices><xsl:text>true</xsl:text></have:AmbulanceServices>
                        </xsl:if>
                        <xsl:if test="starts-with(./data[@field='tair']/text(), 'T')">
                            <have:AirTransportServices><xsl:text>true</xsl:text></have:AirTransportServices>
                        </xsl:if>
                    </have:TransportServicesSubType>
                </have:TransportServicesIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='psya']/text(), 'T') or
                          starts-with(./data[@field='psyp']/text(), 'T')">
                <have:PsychiatricIndicator>
                    <have:PsychiatricSubType>
                        <xsl:if test="starts-with(./data[@field='psya']/text(), 'T')">
                            <have:PsychiatricAdultGeneral>true</have:PsychiatricAdultGeneral>
                        </xsl:if>
                        <xsl:if test="starts-with(./data[@field='psyp']/text(), 'T')">
                            <have:PsychiatricPediatric>true</have:PsychiatricPediatric>
                        </xsl:if>
                    </have:PsychiatricSubType>
                </have:PsychiatricIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='obgy']/text(), 'T')">
                <have:OBGYNIndicator>
                    <have:OBGYN>true</have:OBGYN>
                </have:OBGYNIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='neon']/text(), 'T')">
                <have:Neonatology>true</have:Neonatology>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='pedi']/text(), 'T')">
                <have:Pediatrics>true</have:Pediatrics>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='dial']/text(), 'T')">
                <have:Dialysis>true</have:Dialysis>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='neur']/text(), 'T')">
                <have:NeurologyIndicator>
                    <have:Neurology>true</have:Neurology>
                </have:NeurologyIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='surg']/text(), 'T')">
                <have:SurgeryIndicator>
                    <have:Surgery>true</have:Surgery>
                </have:SurgeryIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='burn']/text(), 'T')">
                <have:Burn>true</have:Burn>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='card']/text(), 'T')">
                <have:CardiologyIndicator>
                    <have:Cardiology>true</have:Cardiology>
                </have:CardiologyIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='trac']/text(), 'T')">
                <have:TraumaCenterIndicator>
                    <have:TraumaCenterServices>true</have:TraumaCenterServices>
                </have:TraumaCenterIndicator>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='infd']/text(), 'T')">
                <have:InfectiousDiseases>true</have:InfectiousDiseases>
            </xsl:if>
            <xsl:if test="starts-with(./data[@field='emsd']/text(), 'T')">
                <have:EmergencyDepartment>true</have:EmergencyDepartment>
            </xsl:if>
        </have:ServiceCoverageStatus>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
