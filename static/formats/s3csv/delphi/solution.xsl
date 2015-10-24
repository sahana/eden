<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Delphi Solution - CSV Import Stylesheet

         CSV fields:
         Group...................delphi_group.name
         Name....................delphi_problem
         Description.............delphi_problem
         Criteria................delphi_problem

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:key name="problems" match="row" use="col[@field='Problem']"/>
    <xsl:key name="groups" match="row" use="col[@field='Group']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Groups -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('groups',
                                                        col[@field='Group'])[1])]">
                <xsl:call-template name="Group"/>
            </xsl:for-each>

            <!-- Problems -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('problems',
                                                        col[@field='Problem'])[1])]">
                <xsl:call-template name="Problem"/>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Create the Solution -->
        <resource name="delphi_solution">
            <reference field="problem_id" resource="delphi_problem">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Problem']"/>
                </xsl:attribute>
            </reference>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Group">
        <xsl:variable name="GroupName" select="col[@field='Group']/text()"/>

        <!-- Create the Problem -->
        <resource name="delphi_group">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$GroupName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$GroupName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Problem">
        <xsl:variable name="ProblemName" select="col[@field='Problem']/text()"/>

        <!-- Create the Problem -->
        <resource name="delphi_problem">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$ProblemName"/>
            </xsl:attribute>
            <reference field="group_id" resource="delphi_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Group']"/>
                </xsl:attribute>
            </reference>
            <data field="name"><xsl:value-of select="$ProblemName"/></data>
        </resource>


    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
