<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Delphi Solution - CSV Import Stylesheet

         - use for import to delphi/solution resource
         - example raw URL usage:
           Let URLpath be the URL to Sahana Eden appliation
           Let Resource be delphi/solution/create
           Let Type be s3csv
           Let CSVPath be the path on the server to the CSV file to be imported
           Let XSLPath be the path on the server to the XSL transform file
           Then in the browser type:

           URLpath/Resource.Type?filename=CSVPath&transform=XSLPath

           You can add a third argument &ignore_errors
         CSV fields:
         Group...................delphi_group.name
         Name....................delphi_problem
         Description.............delphi_problem
         Criteria................delphi_problem

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="ProblemName" select="col[@field='Problem']/text()"/>

        <!-- Create the Problem -->
        <resource name="delphi_problem">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$ProblemName"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$ProblemName"/></data>
        </resource>

        <!-- Create the Solution -->
        <resource name="delphi_solution">
            <reference field="problem_id" resource="delphi_problem">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$ProblemName"/>
                </xsl:attribute>
            </reference>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
