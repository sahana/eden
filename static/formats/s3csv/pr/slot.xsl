<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Availability Slots - CSV Import Stylesheet

         CSV fields:
         Name............................pr_slot.name
         Date Name.......................pr_date_formula.name
         Time Name.......................pr_time_formula.name

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="date" match="row"
             use="col[@field='Date Name']"/>

    <xsl:key name="time" match="row"
             use="col[@field='Time Name']"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Date Formulae -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('date',
                                                                   col[@field='Date Name'])[1])]">
                <xsl:call-template name="Date"/>
            </xsl:for-each>

            <!-- Time Formulae -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('time',
                                                                   col[@field='Time Name'])[1])]">
                <xsl:call-template name="Time"/>
            </xsl:for-each>

            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <resource name="pr_slot">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <reference field="date_formula_id" resource="pr_date_formula">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Date:', col[@field='Date Name'])"/>
                </xsl:attribute>
            </reference>
            <reference field="time_formula_id" resource="pr_time_formula">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('Time:', col[@field='Time Name'])"/>
                </xsl:attribute>
            </reference>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Date">
        <xsl:variable name="DateName" select="col[@field='Date Name']"/>

        <resource name="pr_date_formula">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Date:', $DateName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$DateName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Time">
        <xsl:variable name="TimeName" select="col[@field='Time Name']"/>

        <resource name="pr_time_formula">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('Time:', $TimeName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$TimeName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
