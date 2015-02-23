<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- Templates for Import of CSV Disciplinary Record Data
         used by: disciplinary_type.xsl, person.xsl
    -->

    <!-- ****************************************************************** -->
    <!-- Disciplinary Action Type -->
    <xsl:template name="DisciplinaryActionType">

        <xsl:param name="Field">Name</xsl:param>

        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="Name" select="col[@field=$Field]"/>

        <xsl:if test="$Name!=''">
            <resource name="hrm_disciplinary_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat('DisciplinaryActionType:', $OrgName, ':', $Name)"/>
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
    <!-- Disciplinary Action per Person -->
    <xsl:template name="DisciplinaryAction">

        <xsl:param name="person_tuid"/>
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>

        <resource name="hrm_disciplinary_action">

            <reference field="person_id" resource="pr_person">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$person_tuid"/>
                </xsl:attribute>
            </reference>

            <xsl:variable name="DisciplinaryActionType" select="col[@field='Disciplinary Type']/text()"/>
            <xsl:if test="$DisciplinaryActionType!=''">
                <reference field="disciplinary_type_id" resource="hrm_disciplinary_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('DisciplinaryActionType:', $OrgName, ':', $DisciplinaryActionType)"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <xsl:variable name="DisciplinaryActionDate" select="col[@field='Disciplinary Date']/text()"/>
            <xsl:if test="$DisciplinaryActionDate!=''">
                <data field="date">
                    <xsl:value-of select="$DisciplinaryActionDate"/>
                </data>
            </xsl:if>

            <xsl:variable name="DisciplinaryBody" select="col[@field='Disciplinary Body']/text()"/>
            <xsl:if test="$DisciplinaryBody!=''">
                <data field="disciplinary_body">
                    <xsl:value-of select="$DisciplinaryBody"/>
                </data>
            </xsl:if>

        </resource>

    </xsl:template>

</xsl:stylesheet>
