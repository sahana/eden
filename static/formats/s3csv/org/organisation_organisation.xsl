<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Organisation <> Organisations - CSV Import Stylesheet

         CSV fields:
         Parent...............................parent_id$.name
         Organisation.........................organisation_id$name

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="parent" match="row" use="col[@field='Parent']"/>
    <xsl:key name="organisation" match="row" use="col[@field='Organisation']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>

            <!-- Parents -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('parent',
                                                                       col[@field='Parent'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="Organisation" select="col[@field='Parent']"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Organisations -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('organisation',
                                                                       col[@field='Organisation'])[1])]">
                <xsl:call-template name="Organisation">
                    <xsl:with-param name="Organisation" select="col[@field='Organisation']"/>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Organisation <> Organisations -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <resource name="org_organisation_organisation">

            <reference field="parent_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Parent']"/>
                </xsl:attribute>
            </reference>

            <reference field="organisation_id" resource="org_organisation">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Organisation']"/>
                </xsl:attribute>
            </reference>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Organisation">

        <xsl:param name="Organisation"/>

        <resource name="org_organisation">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Organisation"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Organisation"/></data>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
