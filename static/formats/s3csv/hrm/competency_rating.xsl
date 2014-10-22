<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Competency Ratings - CSV Import Stylesheet

         CSV fields:
         Type............................hrm_skill_type.name
         Name............................hrm_competency_rating.name
         Priority........................hrm_competency_rating.priority

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="skill.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="SkillType" select="col[@field='Type']"/>

        <!-- HRM Competency Rating -->
        <resource name="hrm_competency_rating">
            <reference field="skill_type_id" resource="hrm_skill_type">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="$SkillType"/>
                </xsl:attribute>
            </reference>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="priority"><xsl:value-of select="col[@field='Priority']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
