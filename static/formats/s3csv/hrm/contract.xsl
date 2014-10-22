<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:hrm="http://eden.sahanafoundation.org/hrm">

    <!-- Templates for Import of CSV Contract Information,
         used by: person.xsl 
    -->

    <hrm:contract-terms>
        <hrm:contract-term code="SHORT">short-term</hrm:contract-term>
        <hrm:contract-term code="LONG">long-term</hrm:contract-term>
        <hrm:contract-term code="PERMANENT">permanent</hrm:contract-term>
    </hrm:contract-terms>
    
    <hrm:hours-models>
        <hrm:hours-model code="PARTTIME">part-time</hrm:hours-model>
        <hrm:hours-model code="FULLTIME">full-time</hrm:hours-model>
    </hrm:hours-models>

    <!-- ****************************************************************** -->
    <xsl:template name="Contract">

        <xsl:variable name="ContractTerm"
                      select="col[@field='Contract Term']/text()"/>
        <xsl:variable name="ContractTermCode">
            <xsl:value-of select="document('')//hrm:contract-term[text()=$ContractTerm]/@code"/>
        </xsl:variable>

        <xsl:variable name="HoursModel"
                      select="col[@field='Hours Model']/text()"/>
        <xsl:variable name="HoursModelCode">
            <xsl:value-of select="document('')//hrm:hours-model[text()=$HoursModel]/@code"/>
        </xsl:variable>

        <xsl:if test="$ContractTermCode!='' or $HoursModelCode!=''">
            <resource name="hrm_contract">
                <xsl:if test="$ContractTermCode!=''">
                    <data field="term"><xsl:value-of select="$ContractTermCode"/></data>
                </xsl:if>
                <xsl:if test="$HoursModelCode!=''">
                    <data field="hours"><xsl:value-of select="$HoursModelCode"/></data>
                </xsl:if>
            </resource>
        </xsl:if>

    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
