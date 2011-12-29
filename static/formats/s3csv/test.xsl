<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- Example for the use of ResolveColumnHeader and GetColumnValue templates,
         see labels.xml for a labels resolution map example
    -->

    <xsl:output method="xml"/>

    <!-- Include common templates -->
    <xsl:include href="commons.xsl"/>

    <!-- Resolve all required column headers into variables -->
    <xsl:variable name="PersonGender">
        <xsl:call-template name="ResolveColumnHeader">
            <xsl:with-param name="colname">PersonGender</xsl:with-param>
        </xsl:call-template>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <test>
            <xsl:apply-templates select="//table[1]"/>
        </test>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="table">
        <xsl:apply-templates select="row"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <resource name="pr_person">
            <data field="gender">
                <!-- Get the column value (resolved by option variants where defined),
                     use the column headers variable to find the column -->
                <xsl:call-template name="GetColumnValue">
                    <xsl:with-param name="colhdrs" select="$PersonGender"/>
                </xsl:call-template>
            </data>
        </resource>
    </xsl:template>

</xsl:stylesheet>
