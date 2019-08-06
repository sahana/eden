<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Groups - CSV Import Stylesheet

         CSV fields:
         uuid....................pr_group.uuid (Optional to match contact lists with event types)
         Name....................pr_group.name
         Type....................pr_group.group_type
         Description.............pr_group.description
         Comments.............pr_group.comments
         KV:XX...................Key,Value (Key = XX in column name, value = cell in row)

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
            <data field="description"><xsl:value-of select="col[@field='Description']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>

            <!-- Arbitrary Tags -->
            <xsl:for-each select="col[starts-with(@field, 'KV')]">
                <xsl:call-template name="KeyValue"/>
            </xsl:for-each>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="KeyValue">
        <xsl:variable name="Key" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <xsl:if test="$Value!=''">
            <resource name="pr_group_tag">
                <data field="tag"><xsl:value-of select="$Key"/></data>
                <data field="value"><xsl:value-of select="$Value"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
