<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    
    <!-- Templates for Import of CSV Award Information,
         used by: award_type.xsl (+person.xsl planned)
    -->

    <!-- ****************************************************************** -->
    <!-- Award Type -->
    <xsl:template name="AwardType">

        <xsl:param name="Field">Name</xsl:param>

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="Name" select="col[@field=$Field]"/>

        <xsl:if test="$Name!=''">
            <resource name="hrm_award_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('AwardType:', $OrgName, ':', $Name)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Name"/></data>
                <!-- Link to Organisation -->
                <xsl:if test="$OrgName!=''">
                    <reference field="organisation_id" resource="org_organisation">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="$OrgName"/>
                        </xsl:attribute>
                    </reference>
                </xsl:if>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
