<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- Templates for Import of CSV Award Information,
         used by: award_type.xsl, person.xsl
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
    <!-- Award Information per Person -->
    <xsl:template name="Award">

        <xsl:param name="person_tuid"/>
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="hrm_award" alias="staff_award">

            <reference field="person_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$person_tuid"/>
                </xsl:attribute>
            </reference>

            <xsl:variable name="AwardType" select="col[@field='Award Type']/text()"/>
            <xsl:if test="$AwardType!=''">
                <reference field="award_type_id" resource="hrm_award_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('AwardType:', $OrgName, ':', $AwardType)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <xsl:variable name="AwardDate" select="col[@field='Award Date']/text()"/>
            <xsl:if test="$AwardDate!=''">
                <data field="date">
                    <xsl:value-of select="$AwardDate"/>
                </data>
            </xsl:if>

            <xsl:variable name="AwardingBody" select="col[@field='Awarding Body']/text()"/>
            <xsl:if test="$AwardingBody!=''">
                <data field="awarding_body">
                    <xsl:value-of select="$AwardingBody"/>
                </data>
            </xsl:if>

        </resource>

    </xsl:template>

</xsl:stylesheet>
