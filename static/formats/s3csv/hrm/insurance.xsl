<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- Templates for Import of CSV Insurance Information,
         used by: person.xsl 
    -->

    <!-- ****************************************************************** -->
    <xsl:template name="Insurance">

        <!-- Social Insurance -->
        <xsl:variable name="SocialInsuranceNumber"
                      select="col[@field='Social Insurance Number']/text()"/>
        <xsl:if test="$SocialInsuranceNumber!=''">
            <resource name="hrm_insurance">
                <data field="type" value="SOCIAL"/>
                <data field="insurance_number">
                    <xsl:value-of select="$SocialInsuranceNumber"/>
                </data>
            <xsl:variable name="SocialInsurancePlace"
                          select="col[@field='Social Insurance Place']/text()"/>
                <xsl:if test="$SocialInsurancePlace!=''">
                    <data field="insurer">
                        <xsl:value-of select="$SocialInsurancePlace"/>
                    </data>
                </xsl:if>
            </resource>
        </xsl:if>

        <!-- Health Insurance -->
        <xsl:variable name="HealthInsuranceNumber"
                      select="col[@field='Health Insurance Number']/text()"/>
        <xsl:if test="$HealthInsuranceNumber!=''">
            <resource name="hrm_insurance">
                <data field="type" value="HEALTH"/>
                <data field="insurance_number">
                    <xsl:value-of select="$HealthInsuranceNumber"/>
                </data>
            <xsl:variable name="HealthCareProvider"
                          select="col[@field='Health Care Provider']/text()"/>
                <xsl:if test="$HealthCareProvider!=''">
                    <data field="provider">
                        <xsl:value-of select="$HealthCareProvider"/>
                    </data>
                </xsl:if>
            </resource>
        </xsl:if>

    </xsl:template>
    <!-- ****************************************************************** -->
    
</xsl:stylesheet>
