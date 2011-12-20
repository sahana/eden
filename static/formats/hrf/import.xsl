<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************

        Google Resource Finder / Hospitals

         CSV Import Stylesheet / 2011-01-22 / Dominic König <dominic@aidiq.com>

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

        @todo: automatically report persons missing if no explicit found-note?

    *********************************************************************** -->

    <xsl:output method="xml"/>
    <xsl:include href="../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <!-- Root -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table[1]"/>
        </s3xml>
    </xsl:template>

    <xsl:template match="table">
        <xsl:apply-templates select="./row"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Hospital -->
    <xsl:template match="row">
        <xsl:if test="./col[@field='name']/text()!=''">
            <xsl:variable name="facility_type">
                <xsl:choose>
                    <xsl:when test="./col[@field='category']/text()='HOSPITAL'">1</xsl:when>
                    <xsl:when test="./col[@field='category']/text()='CLINIC'">11</xsl:when>
                    <xsl:otherwise>98</xsl:otherwise>
                </xsl:choose>
            </xsl:variable>
            <xsl:if test="$facility_type!='98'">
                <resource name="hms_hospital">
                    <xsl:call-template name="HospitalID">
                        <xsl:with-param name="field">gov_uuid</xsl:with-param>
                    </xsl:call-template>
                    <data field="name">
                        <xsl:value-of select="./col[@field='name']"/>
                    </data>
                    <data field="facility_type">
                        <xsl:value-of select="$facility_type"/>
                    </data>
                    <xsl:call-template name="HospitalBedCapacity"/>
                    <xsl:call-template name="HospitalLocation"/>
                </resource>
            </xsl:if>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- HospitalLocation -->
    <xsl:template name="HospitalLocation">
        <reference field="location_id" resource="gis_location">
            <resource name="gis_location">
                <data field="name">
                    <xsl:value-of select="./col[@field='name']"/>
                </data>
                <data field="lat">
                    <xsl:value-of select="./col[@field='latitude']"/>
                </data>
                <data field="lon">
                    <xsl:value-of select="./col[@field='longitude']"/>
                </data>
            </resource>
        </reference>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- HospitalBedCapacity -->
    <xsl:template name="HospitalBedCapacity">
        <xsl:if test="./col[@field='total_beds']/text()!=''">
            <resource name="hms_bed_capacity">
                <xsl:call-template name="HospitalID">
                    <xsl:with-param name="field">unit_id</xsl:with-param>
                </xsl:call-template>
                <data field="bed_type" value="99"/>
                <data field="beds_baseline">
                    <xsl:value-of select="./col[@field='total_beds']/text()"/>
                </data>
                <data field="beds_available">
                    <xsl:value-of select="./col[@field='available_beds']/text()"/>
                </data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Hospital ID -->
    <xsl:template name="HospitalID">
        <xsl:param name="field"/>
        <!-- column name has changed from version to version, need to choose -->
        <xsl:choose>
            <xsl:when test="./col[@field='healthc_id']/text()!=''">
                <data>
                    <xsl:attribute name="field">
                        <xsl:value-of select="$field"/>
                    </xsl:attribute>
                    <xsl:value-of select="./col[@field='healthc_id']/text()"/>
                </data>
            </xsl:when>
            <xsl:when test="./col[@field='id']/text()!=''">
                <data>
                    <xsl:attribute name="field">
                        <xsl:value-of select="$field"/>
                    </xsl:attribute>
                    <xsl:value-of select="./col[@field='id']/text()"/>
                </data>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
