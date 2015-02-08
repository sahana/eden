<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Certificate Skill Equivalences - CSV Import Stylesheet

         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be hrm/competency_rating/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors
         CSV fields:
         Certificate......................hrm_certificate_skill.certificate_id
         Skill............................hrm_certificate_skill.skill_id
         Competency.......................hrm_certificate_skill.competency_id

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:key name="skill" match="row" use="col[@field='Skill']"/>
    <xsl:key name="competency" match="row" use="col[@field='Competency']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Skills -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('skill', col[@field='Skill'])[1])]">
                <xsl:call-template name="Skill"/>
            </xsl:for-each>

            <!-- Competencies -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('competency', col[@field='Competency'])[1])]">
                <xsl:call-template name="Competency"/>
            </xsl:for-each>

            <!-- Certificates -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="SkillName" select="col[@field='Skill']/text()"/>
        <xsl:variable name="CompetencyName" select="col[@field='Competency']/text()"/>
        <xsl:variable name="CertificateName" select="col[@field='Certificate']/text()"/>

        <!-- HRM Certificate -->
        <resource name="hrm_certificate">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$CertificateName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$CertificateName"/></data>
        </resource>

        <!-- HRM Certificate_Skill -->
        <resource name="hrm_certificate_skill">
            <!-- Link to Certificate -->
            <reference field="certificate_id" resource="hrm_certificate">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$CertificateName"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Skill -->
            <reference field="skill_id" resource="hrm_skill">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$SkillName"/>
                </xsl:attribute>
            </reference>
            <!-- Link to Competency -->
            <reference field="competency_id" resource="hrm_competency_rating">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$CompetencyName"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template name="Skill">
        <xsl:variable name="SkillName" select="col[@field='Skill']/text()"/>

        <resource name="hrm_skill">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$SkillName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$SkillName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

    <xsl:template name="Competency">
        <xsl:variable name="CompetencyName" select="col[@field='Competency']/text()"/>

        <resource name="hrm_competency_rating">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$CompetencyName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$CompetencyName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
