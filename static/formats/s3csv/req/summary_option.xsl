<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Request Summary Options - CSV Import Stylesheet

         CSV fields:
         Name............................req_summary_option.name
         Comments........................req_summary_option.comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <!--<xsl:key name="orgs"
             match="row"
             use="col[@field='Organisation']"/>-->

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Organisations -->
            <!--<xsl:for-each select="//row[generate-id(.)=generate-id(key('orgs', col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation"/>
            </xsl:for-each>-->

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!--<xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>-->

        <xsl:variable name="SummaryOption" select="col[@field='Name']"/>
        <resource name="req_summary_option">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$SummaryOption"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$SummaryOption"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            
            <!-- Link to Organisation to filter lookup lists -->
            <!--<xsl:if test="$OrgName!=''">
                <reference field="organisation_id" resource="org_organisation">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$OrgName"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>-->
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
