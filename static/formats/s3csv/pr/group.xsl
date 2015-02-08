<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Groups - CSV Import Stylesheet

         CSV fields:
         Name............................pr_group.name
         Type............................pr_group.group_type
         uuid............................pr_group.uuid (Optional to match contact lists with event types)

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

        <!-- PR Group -->
        <xsl:variable name="GroupName" select="col[@field='Name']"/>
        <resource name="pr_group">
            <xsl:if test="col[@field='uuid']!=''">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="col[@field='uuid']"/>
                </xsl:attribute>
            </xsl:if>
            <data field="name"><xsl:value-of select="$GroupName"/></data>
            <data field="group_type"><xsl:value-of select="col[@field='Type']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
