<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Courses - CSV Import Stylesheet

         CSV fields:
         Code............................hrm_course.code
         Name............................hrm_course.name
         Organisation....................hrm_course.organisation_id
         Certificate.....................hrm_course_certificate.certificate_id

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:variable name="CertPrefix" select="'Cert:'"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="certs"
             match="row"
             use="col[@field='Certificate']"/>

    <xsl:key name="orgs"
             match="row"
             use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Certificates -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('certs',
                                                        col[@field='Certificate'])[1])]">
                <xsl:call-template name="Certificate"/>
            </xsl:for-each>

            <!-- Orgs -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('orgs',
                                                        col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>

            <!-- Courses -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="CertName" select="col[@field='Certificate']/text()"/>
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <!-- HRM Course -->
        <resource name="hrm_course">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="code"><xsl:value-of select="col[@field='Code']"/></data>
            <xsl:if test="$CertName!=''">
                <resource name="hrm_course_certificate">
                    <reference field="certificate_id" resource="hrm_certificate">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($CertPrefix, $CertName)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
            <xsl:if test="$OrgName!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Certificate">

        <xsl:variable name="CertName" select="col[@field='Certificate']/text()"/>
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="hrm_certificate">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($CertPrefix, $CertName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$CertName"/></data>
            <xsl:if test="$OrgName!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$OrgName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$OrgName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
