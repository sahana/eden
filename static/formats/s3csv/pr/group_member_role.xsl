<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Group Member Roles - CSV Import Stylesheet

         CSV column...........Format..........Content

         Group Type...........string..........Group Type
         Name.................string..........Role Name
         Comments.............string..........Comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="./table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <xsl:variable name="Name" select="col[@field='Name']/text()"/>
        <xsl:if test="$Name!=''">
            <resource name="pr_group_member_role">
                <data field="name">
                    <xsl:value-of select="$Name"/>
                </data>
                <xsl:variable name="GroupType" select="col[@field='Group Type']/text()"/>
                <data field="group_type">
                    <xsl:choose>
                        <xsl:when test="$GroupType='Family'">1</xsl:when>
                        <xsl:when test="$GroupType='Tourist Group'">2</xsl:when>
                        <xsl:when test="$GroupType='Relief Team'">3</xsl:when>
                        <xsl:when test="$GroupType='Mailing Lists'">5</xsl:when>
                        <xsl:when test="$GroupType='Case'">7</xsl:when>
                        <xsl:otherwise>4</xsl:otherwise>
                    </xsl:choose>
                </data>
                <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>
                <xsl:if test="$Comments!=''">
                    <data field="comments">
                        <xsl:value-of select="$Comments"/>
                    </data>
                </xsl:if>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
</xsl:stylesheet>
