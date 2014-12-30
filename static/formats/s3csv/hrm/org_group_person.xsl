<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- Templates for Import of CSV Org Group Links
         used by: person.xsl
    -->

    <!-- ****************************************************************** -->
    <!-- OrgGroup -->
    <xsl:template name="OrgGroup">

        <xsl:param name="Field">Name</xsl:param>

        <xsl:variable name="Name">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Field"/>
            </xsl:call-template>
        </xsl:variable>

        <xsl:if test="$Name!=''">
            <resource name="org_group">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('OrgGroup:', $Name)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Name"/></data>
            </resource>
        </xsl:if>

    </xsl:template>
    
    <!-- ****************************************************************** -->
    <!-- OrgGroup/Person Link -->
    <xsl:template name="OrgGroupPerson">

        <xsl:param name="Field">OrgGroup</xsl:param>
        
        <xsl:variable name="Name">
            <xsl:call-template name="GetColumnValue">
                <xsl:with-param name="colhdrs" select="$Field"/>
            </xsl:call-template>
        </xsl:variable>
        <xsl:if test="$Name!=''">
            <resource name="org_group_person">
                <reference field="org_group_id" resource="org_group">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('OrgGroup:', $Name)"/>
                    </xsl:attribute>
                </reference>
            </resource>
        </xsl:if>

    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
