<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
            xmlns:have="urn:oasis:names:tc:emergency:EDXL:HAVE:1.0"
            xmlns:gml="http://www.opengis.net/gml"
            xmlns:xnl="urn:oasis:names:tc:ciq:xnl:3"
            xmlns:xal="urn:oasis:names:tc:ciq:xal:3"
            xmlns:xpil="urn:oasis:names:tc:ciq:xpil:3">

    <!-- EDXL-HAVE Import Templates

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
    <!-- Root element -->
    <xsl:template match="/">
        <xsl:apply-templates select="./have:HospitalStatus"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- HospitalStatus -->
    <xsl:template match="have:HospitalStatus">
        <s3xml>
            <xsl:apply-templates select="./have:Hospital"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Hospital -->
    <xsl:template match="have:Hospital">
        <resource name="hms_hospital">
            <!-- LastUpdateTime -->
            <xsl:if test="./have:LastUpdateTime/text()">
                <xsl:attribute name="modified_on">
                    <xsl:choose>
                        <xsl:when test="contains(./have:LastUpdateTime/text(), 'T')">
                            <xsl:value-of select="./have:LastUpdateTime/text()"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="datetime2iso">
                                <xsl:with-param name="datetime" select="./have:LastUpdateTime/text()"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </xsl:if>
            <!-- Sub-Elements -->
            <xsl:apply-templates select="./have:Organization"/>
            <xsl:call-template name="StatusReport"/>
            <xsl:apply-templates select="have:HospitalFacilityStatus/have:Activity24Hr"/>
            <xsl:apply-templates select="./have:HospitalBedCapacityStatus"/>
            <xsl:apply-templates select="./have:ServiceCoverageStatus[1]"/>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Organization -->
    <xsl:template match="have:Organization">
        <!-- Sub-Elements -->
        <xsl:apply-templates select="./have:OrganizationInformation"/>
        <xsl:apply-templates select="./have:OrganizationGeoLocation"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Status report -->
    <xsl:template name="StatusReport">
        <resource name="hms_status">
            <xsl:apply-templates select="./have:EmergencyDepartmentStatus"/>
            <xsl:apply-templates select="have:HospitalFacilityStatus/have:FacilityStatus"/>
            <xsl:apply-templates select="have:HospitalFacilityStatus/have:ClinicalStatus"/>
            <xsl:apply-templates select="have:HospitalFacilityStatus/have:MorgueCapacity"/>
            <xsl:apply-templates select="have:HospitalFacilityStatus/have:SecurityStatus"/>
            <xsl:apply-templates select="./have:HospitalResourceStatus"/>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- EmergencyDepartmentStatus -->
    <xsl:template match="have:EmergencyDepartmentStatus">
        <xsl:variable name="status">
            <xsl:call-template name="lowercase">
                <xsl:with-param name="string" select="./have:EMSTrafficStatus/text()"/>
            </xsl:call-template>
        </xsl:variable>
        <data field="ems_status">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="$status='normal'">1</xsl:when>
                    <xsl:when test="$status='advisory'">2</xsl:when>
                    <xsl:when test="$status='closed'">3</xsl:when>
                </xsl:choose>
            </xsl:attribute>
        </data>
        <xsl:if test="./have:EMSTrafficReason/text()!=''">
            <data field="ems_reason">
                <xsl:value-of select="./have:EMSTrafficReason/text()"/>
            </data>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- HospitalBedCapacityStatus -->
    <xsl:template match="have:HospitalBedCapacityStatus">
        <xsl:apply-templates select="./have:BedCapacity"/>
    </xsl:template>

    <xsl:template match="have:BedCapacity">
        <resource name="hms_bed_capacity">
            <xsl:variable name="bedtype">
                <xsl:call-template name="lowercase">
                    <xsl:with-param name="string" select="./have:BedType/text()"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:variable name="bedtype_code">
                <xsl:choose>
                    <xsl:when test="$bedtype='adulticu'">1</xsl:when>
                    <xsl:when test="$bedtype='pediatricicu'">2</xsl:when>
                    <xsl:when test="$bedtype='neonatalicu'">3</xsl:when>
                    <xsl:when test="$bedtype='emergencydepartment'">4</xsl:when>
                    <xsl:when test="$bedtype='nurserybeds'">5</xsl:when>
                    <xsl:when test="$bedtype='medicalsurgical'">6</xsl:when>
                    <xsl:when test="$bedtype='rehablongtermcare'">7</xsl:when>
                    <xsl:when test="$bedtype='burn'">8</xsl:when>
                    <xsl:when test="$bedtype='pediatrics'">9</xsl:when>
                    <xsl:when test="$bedtype='adultpsychiatric'">10</xsl:when>
                    <xsl:when test="$bedtype='pediatricpsychiatric'">11</xsl:when>
                    <xsl:when test="$bedtype='negativeflowisolation'">12</xsl:when>
                    <xsl:when test="$bedtype='otherisolation'">13</xsl:when>
                    <xsl:when test="$bedtype='operatingrooms'">14</xsl:when>
                    <xsl:when test="$bedtype='choleratreatment'">15</xsl:when>
                </xsl:choose>
            </xsl:variable>
            <xsl:variable name="uid">
                <xsl:value-of select="../../have:Organization/have:OrganizationInformation/xnl:OrganisationName/@xnl:ID"/>
            </xsl:variable>
            <data field="unit_id">
                <xsl:value-of select="concat($uid, '-', $bedtype_code)"/>
            </data>
            <data field="bed_type">
                <xsl:attribute name="value">
                    <xsl:value-of select="$bedtype_code"/>
                </xsl:attribute>
            </data>
            <data field="beds_available">
                <xsl:attribute name="value">
                    <xsl:value-of select="sum(./have:AvailableCount)"/>
                </xsl:attribute>
            </data>
            <data field="beds_baseline">
                <xsl:attribute name="value">
                    <xsl:value-of select="sum(./have:BaselineCount)"/>
                </xsl:attribute>
            </data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- ServiceCoverageStatus -->
    <xsl:template match="have:ServiceCoverageStatus">
        <resource name="hms_services">
            <xsl:if test=".//have:AmbulanceServices/text()='true'">
                <data field="tran" value="True"/>
            </xsl:if>
            <xsl:if test=".//have:AirTransportServices/text()='true'">
                <data field="tair" value="True"/>
            </xsl:if>
            <xsl:if test=".//have:PsychiatricAdultGeneral/text()='true'">
                <data field='psya' value="True"/>
            </xsl:if>
            <xsl:if test=".//have:PsychiatricPediatric/text()='true'">
                <data field='psyp' value="True"/>
            </xsl:if>
            <xsl:if test=".//have:OBGYN/text()='true'">
                <data field='obgy' value="True"/>
            </xsl:if>
            <xsl:if test=".//have:Neonatology/text()='true'">
                <data field='neon' value="True"/>
            </xsl:if>
            <xsl:if test=".//have:Pediatrics/text()='true'">
                <data field='pedi' value="True"/>
            </xsl:if>
            <xsl:if test=".//have:Dialysis/text()='true'">
                <data field='dial' value="True"/>
            </xsl:if>
            <xsl:if test=".//have:Neurology/text()='true'">
                <data field='neur' value="True"/>
            </xsl:if>
            <xsl:if test=".//have:Surgery/text()='true'">
                <data field='surg' value="True"/>
            </xsl:if>
            <xsl:if test=".//have:Burn/text()='true'">
                <data field='burn' value="True"/>
            </xsl:if>
            <xsl:if test=".//have:Cardiology/text()='true'">
                <data field='card' value="True"/>
            </xsl:if>
            <xsl:if test=".//have:TraumaCenterServices/text()='true'">
                <data field='trac' value="True"/>
            </xsl:if>
            <xsl:if test=".//have:InfectiousDiseases/text()='true'">
                <data field='infd' value="True"/>
            </xsl:if>
            <xsl:if test=".//have:EmergencyDepartment/text()='true'">
                <data field='emsd' value="True"/>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- HospitalResourceStatus -->
    <xsl:template match="have:HospitalResourceStatus">
        <!-- Sub-Elements -->
        <xsl:apply-templates select="./have:FacilityOperations"/>
        <xsl:apply-templates select="./have:ClinicalOperations"/>
        <xsl:apply-templates select="./have:Staffing"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- OrganizationInformation -->
    <xsl:template match="have:OrganizationInformation">
        <!-- Sub-Elements -->
        <xsl:apply-templates select="./xnl:OrganisationName"/>
        <xsl:apply-templates select="./xpil:ContactNumbers"/>
        <xsl:apply-templates select="./xpil:Addresses"/>
        <xsl:apply-templates select="./xpil:ElectronicAddressIdentifiers"/>
        <!-- Facility Type (assuming "Hospital") -->
        <data field="facility_type" value="1">Hospital</data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- OrganizationGeoLocation -->
    <xsl:template match="have:OrganizationGeoLocation">
        <xsl:variable name="location"
                      select="./gml:Point/gml:coordinates/text()"/>
        <xsl:variable name="location_id"
                      select="./gml:Point/@gml:id"/>
        <xsl:variable name="name"
                      select="../have:OrganizationInformation/xnl:OrganisationName/xnl:NameElement[1]/text()"/>
        <xsl:if test="$location">
            <reference field="location_id" resource="gis_location">
                <resource name="gis_location">
                    <xsl:if test="$location_id">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="$location_id"/>
                        </xsl:attribute>
                    </xsl:if>
                    <data field="name">
                        <xsl:value-of select="$name"/>
                    </data>
                    <data field="gis_feature_type" value="1">Point</data>
                    <data field="lat">
                        <xsl:value-of select="normalize-space(substring-before($location, ','))"/>
                    </data>
                    <data field="lon">
                        <xsl:value-of select="normalize-space(substring-after($location, ','))"/>
                    </data>
                </resource>
            </reference>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- OrganisationName -->
    <xsl:template match="xnl:OrganisationName">
        <!-- @todo: import alternative names -->
        <xsl:variable name="name"
                      select="./xnl:NameElement[1]/text()"/>
        <xsl:variable name="uuid_provided"
                      select="./@xnl:ID"/>
        <xsl:if test="$uuid_provided">
            <data field="gov_uuid">
                <xsl:value-of select="$uuid_provided"/>
            </data>
        </xsl:if>
        <data field="name">
            <xsl:value-of select="$name"/>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Contact Numbers -->
    <xsl:template match="xpil:ContactNumbers">
        <data field="phone_exchange">
            <xsl:value-of select="./xpil:ContactNumber[@xpil:MediaType='Telephone' and @xpil:ContactNature='Exchange'][1]/xpil:ContactNumberElement/text()"/>
        </data>
        <data field="phone_business">
            <xsl:value-of select="./xpil:ContactNumber[@xpil:MediaType='Telephone' and @xpil:ContactNature='Business'][1]/xpil:ContactNumberElement/text()"/>
        </data>
        <data field="phone_emergency">
            <xsl:value-of select="./xpil:ContactNumber[@xpil:MediaType='Telephone' and @xpil:ContactNature='Emergency'][1]/xpil:ContactNumberElement/text()"/>
        </data>
        <data field="fax">
            <xsl:value-of select="./xpil:ContactNumber[@xpil:MediaType='Fax'][1]/xpil:ContactNumberElement/text()"/>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Addresses -->
    <xsl:template match="xpil:Addresses">
        <xsl:for-each select=".//xal:FreeTextAddress[1]">
            <data field="address"><xsl:value-of select=".//text()"/></data>
        </xsl:for-each>
        <xsl:for-each select=".//xal:Locality[1]">
            <data field="city"><xsl:value-of select=".//text()"/></data>
        </xsl:for-each>
        <xsl:for-each select=".//xal:PostCode[1]">
            <data field="postcode"><xsl:value-of select=".//text()"/></data>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Electronic Address Identifiers -->
    <xsl:template match="xpil:ElectronicAddressIdentifiers">
        <xsl:for-each select="./xpil:ElectronicAddressIdentifier[@xpil:Type='EMAIL'][1]">
            <data field="email"><xsl:value-of select=".//text()"/></data>
        </xsl:for-each>
        <xsl:for-each select="./xpil:ElectronicAddressIdentifier[@xpil:Type='URL'][1]">
            <data field="website"><xsl:value-of select=".//text()"/></data>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- FacilityStatus -->
    <xsl:template match="have:FacilityStatus">
        <xsl:variable name="status">
            <xsl:call-template name="lowercase">
                <xsl:with-param name="string" select="./text()"/>
            </xsl:call-template>
        </xsl:variable>
        <data field="facility_status">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="$status='normal'">1</xsl:when>
                    <xsl:when test="$status='compromised'">2</xsl:when>
                    <xsl:when test="$status='evacuating'">3</xsl:when>
                    <xsl:when test="$status='closed'">4</xsl:when>
                </xsl:choose>
            </xsl:attribute>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Clinical Status -->
    <xsl:template match="have:ClinicalStatus">
        <xsl:variable name="status">
            <xsl:call-template name="lowercase">
                <xsl:with-param name="string" select="./text()"/>
            </xsl:call-template>
        </xsl:variable>
        <data field="morgue_status">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="$status='normal'">1</xsl:when>
                    <xsl:when test="$status='full'">2</xsl:when>
                    <xsl:when test="$status='closed'">3</xsl:when>
                </xsl:choose>
            </xsl:attribute>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- MorgueCapacity -->
    <xsl:template match="have:MorgueCapacity">
        <xsl:variable name="status">
            <xsl:call-template name="lowercase">
                <xsl:with-param name="string" select="./have:MorgueCapacityStatus/text()"/>
            </xsl:call-template>
        </xsl:variable>
        <data field="morgue_status">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="$status='open'">1</xsl:when>
                    <xsl:when test="$status='full'">2</xsl:when>
                    <xsl:when test="$status='exceeded'">3</xsl:when>
                    <xsl:when test="$status='closed'">4</xsl:when>
                </xsl:choose>
            </xsl:attribute>
        </data>
        <xsl:if test="./have:MorgueCapacityUnits/text()!=''">
            <data field="morgue_units">
                <xsl:value-of select="./have:MorgueCapacityUnits/text()"/>
            </data>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- SecurityStatus -->
    <xsl:template match="have:SecurityStatus">
        <xsl:variable name="status">
            <xsl:call-template name="lowercase">
                <xsl:with-param name="string" select="./text()"/>
            </xsl:call-template>
        </xsl:variable>
        <data field="security_status">
            <xsl:attribute name="value">
                <xsl:choose>
                    <xsl:when test="$status='normal'">1</xsl:when>
                    <xsl:when test="$status='elevated'">2</xsl:when>
                    <xsl:when test="$status='restrictedaccess'">3</xsl:when>
                    <xsl:when test="$status='lockdown'">4</xsl:when>
                    <xsl:when test="$status='quarantine'">5</xsl:when>
                    <xsl:when test="$status='closed'">6</xsl:when>
                </xsl:choose>
            </xsl:attribute>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Activity24Hr -->
    <xsl:template match="have:Activity24Hr">
        <xsl:if test="../../have:LastUpdateTime/text()">
            <resource name="hms_activity">
                <data field="date">
                    <xsl:choose>
                        <xsl:when test="contains(../../have:LastUpdateTime/text(), 'T')">
                            <xsl:value-of select="../../have:LastUpdateTime/text()"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="datetime2iso">
                                <xsl:with-param name="datetime" select="../../have:LastUpdateTime/text()"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </data>
                <data field="admissions24">
                    <xsl:value-of select="./have:Admissions/text()"/>
                </data>
                <data field="discharges24">
                    <xsl:value-of select="./have:Discharges/text()"/>
                </data>
                <data field="deaths24">
                    <xsl:value-of select="./have:Deaths/text()"/>
                </data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Facility Operations -->
    <xsl:template match="have:FacilityOperations">
        <xsl:variable name="facility_operations">
            <xsl:call-template name="ResourceStatusOptions">
                <xsl:with-param name="value" select="./text()"/>
            </xsl:call-template>
        </xsl:variable>
        <data field="facility_operations">
            <xsl:attribute name="value">
                <xsl:value-of select="$facility_operations"/>
            </xsl:attribute>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Clinical Operations -->
    <xsl:template match="have:ClinicalOperations">
        <xsl:variable name="clinical_operations">
            <xsl:call-template name="ResourceStatusOptions">
                <xsl:with-param name="value" select="./text()"/>
            </xsl:call-template>
        </xsl:variable>
        <data field="clinical_operations">
            <xsl:attribute name="value">
                <xsl:value-of select="$clinical_operations"/>
            </xsl:attribute>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Staffing -->
    <xsl:template match="have:Staffing">
        <xsl:variable name="staffing">
            <xsl:call-template name="ResourceStatusOptions">
                <xsl:with-param name="value" select="./text()"/>
            </xsl:call-template>
        </xsl:variable>
        <data field="staffing">
            <xsl:attribute name="value">
                <xsl:value-of select="$staffing"/>
            </xsl:attribute>
        </data>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- ResourceStatusOptions DRY Helper -->
    <xsl:template name="ResourceStatusOptions">
        <xsl:param name="value"/>
        <xsl:variable name="status">
            <xsl:call-template name="lowercase">
                <xsl:with-param name="string" select="$value"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$value='adequate'">1</xsl:when>
            <xsl:otherwise>2</xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
