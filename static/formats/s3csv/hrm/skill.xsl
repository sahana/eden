<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Skills - CSV Import Stylesheet

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
         Type............................hrm_skill_type.name
         Name............................hrm_skill.name
         Comments........................hrm_skill.comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:key name="types" match="row" use="col[@field='Type']/text()"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('types',
                                                        col[@field='Type']/text())[1])]">
                <xsl:call-template name="SkillType"/>
            </xsl:for-each>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="SkillType" select="col[@field='Type']"/>

        <!-- HRM Skill -->
        <resource name="hrm_skill">
            <reference field="skill_type_id" resource="hrm_skill_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$SkillType"/>
                </xsl:attribute>
            </reference>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="SkillType">
        <xsl:variable name="SkillType" select="col[@field='Type']"/>

        <resource name="hrm_skill_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$SkillType"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$SkillType"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
