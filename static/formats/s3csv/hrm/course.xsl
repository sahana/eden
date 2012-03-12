<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Courses - CSV Import Stylesheet

         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be hrm/skill/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors
         CSV fields:
         Name............................hrm_course.name
         Certificate.....................hrm_course_certificate.certificate_id

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:variable name="CertPrefix" select="'Cert:'"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="certs"
             match="row"
             use="col[@field='Certificate']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Certificates -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('certs',
                                                        col[@field='Certificate'])[1])]">
                <xsl:call-template name="Certificate"/>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="CourseName" select="col[@field='Name']"/>
        <xsl:variable name="CertName" select="col[@field='Certificate']/text()"/>

        <!-- HRM Course -->
        <resource name="hrm_course">
            <data field="name"><xsl:value-of select="$CourseName"/></data>
            <xsl:if test="$CertName!=''">
                <resource name="hrm_course_certificate">
                    <reference field="certificate_id" resource="hrm_certificate">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($CertPrefix, $CertName)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Certificate">

        <xsl:variable name="CertName" select="col[@field='Certificate']/text()"/>

        <resource name="hrm_certificate">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($CertPrefix, $CertName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$CertName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
