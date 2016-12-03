<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Project Beneficiary Types - CSV Import Stylesheet

         CSV column...........Format..........Content

         Name.................string..........Type Name
         Description..........string..........Type Description
         Total................string..........Total

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="total" match="row" use="col[@field='Total']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Totals -->
            <xsl:for-each select="//row[generate-id(.)=
                                        generate-id(key('total',
                                                        col[@field='Total'])[1])]">
                <xsl:call-template name="Total" />
            </xsl:for-each>

            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="total" select="col[@field='Total']"/>

        <resource name="project_beneficiary_type">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <xsl:if test="$total!=''">
                <reference field="total_id" resource="project_beneficiary_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('project_beneficiary_type/',$total)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Total">
        <xsl:variable name="total" select="col[@field='Total']"/>

        <xsl:if test="$total!=''">
            <resource name="project_beneficiary_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('project_beneficiary_type/',$total)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$total"/></data>
            </resource>
        </xsl:if>

    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
