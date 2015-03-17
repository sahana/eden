<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- Templates for Import of CSV Beneficiary Information,
         used by: location.xsl, activity.xsl
    -->

    <!-- ****************************************************************** -->
    <!-- Beneficiary Type, called in context of "Beneficiaries:TypeName" columns -->
    <xsl:template name="BeneficiaryType">

        <xsl:variable name="TypeStr" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="BeneficiaryType">
            <xsl:choose>
                <xsl:when test="contains($TypeStr, ':')">
                    <xsl:value-of select="normalize-space(substring-after($TypeStr, ':'))"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$TypeStr"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <resource name="project_beneficiary_type">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat('BNFType:', $BeneficiaryType)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$BeneficiaryType"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Beneficiary Number, called in context of "Beneficiaries:TypeName" columns -->
    <xsl:template name="Beneficiaries">

        <xsl:param name="ProjectName"/>
        <xsl:param name="ActivityName"/>

        <xsl:variable name="TypeStr" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="BeneficiaryType">
            <xsl:choose>
                <xsl:when test="contains($TypeStr, ':')">
                    <xsl:value-of select="normalize-space(substring-after($TypeStr, ':'))"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$TypeStr"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="ActivityType">
            <xsl:if test="contains($TypeStr, ':')">
                <xsl:value-of select="normalize-space(substring-before($TypeStr, ':'))"/>
            </xsl:if>
        </xsl:variable>

        <xsl:variable name="Number" select="text()"/>
        <xsl:variable name="Value">
            <xsl:choose>
                <xsl:when test="contains($Number, '/')">
                    <xsl:value-of select="substring-before($Number, '/')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$Number"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:variable name="TargetColumn" select="concat('Targeted', @field)"/>
        <xsl:variable name="TargetNumber" select="../col[@field=$TargetColumn]/text()"/>
        <xsl:variable name="TargetValue">
            <xsl:choose>
                <xsl:when test="contains($Number, '/')">
                    <xsl:value-of select="substring-after($Number, '/')"/>
                </xsl:when>
                <xsl:when test="$TargetNumber!=''">
                    <xsl:value-of select="$TargetNumber"/>
                </xsl:when>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$Value!='' or $TargetValue!=''">
            <resource name="project_beneficiary">
                <xsl:if test="$ProjectName!='' and $ActivityName !=''">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('BNFNumber:',
                                                     $ProjectName, '/',
                                                     $ActivityName, '/',
                                                     $BeneficiaryType)"/>
                    </xsl:attribute>
                </xsl:if>

                <reference field="parameter_id" resource="project_beneficiary_type">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat('BNFType:', $BeneficiaryType)"/>
                    </xsl:attribute>
                </reference>

                <xsl:if test="$Value!=''">
                    <data field="value"><xsl:value-of select="$Value"/></data>
                </xsl:if>
                <xsl:if test="$TargetValue!=''">
                    <data field="target_value"><xsl:value-of select="$TargetValue"/></data>
                </xsl:if>

                <xsl:if test="$ActivityType!=''">
                    <resource name="project_beneficiary_activity_type">
                        <reference field="activity_type_id">
                            <resource name="project_activity_type">
                                <data field="name">
                                    <xsl:value-of select="$ActivityType"/>
                                </data>
                            </resource>
                        </reference>
                    </resource>
                </xsl:if>

            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
