<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Organisation Group Types - CSV Import Stylesheet

         CSV column...........Format..........Content

         Type.................string..........Type Name
         Code.................string..........Type Code
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
        <xsl:variable name="TypeName" select="col[@field='Type']/text()"/>
        <xsl:if test="$TypeName!=''">
            <resource name="org_group_type">
                <data field="name"><xsl:value-of select="$TypeName"/></data>
                <data field="code"><xsl:value-of select="col[@field='Code']/text()"/></data>
                <data field="comments"><xsl:value-of select="col[@field='Comments']/text()"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
