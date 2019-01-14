<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Forums - CSV Import Stylesheet

         CSV fields:
         uuid............................pr_forum.uuid
         Name............................pr_forum.name
         Type............................pr_forum.forum_type
         Comments........................pr_forum.comments

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- PR Forum -->
        <xsl:variable name="ForumName" select="col[@field='Name']"/>
        <resource name="pr_forum">
            <xsl:if test="col[@field='uuid']!=''">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="col[@field='uuid']"/>
                </xsl:attribute>
            </xsl:if>
            <data field="name"><xsl:value-of select="$ForumName"/></data>
            <data field="forum_type"><xsl:value-of select="col[@field='Type']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
