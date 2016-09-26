<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         RSS Channels - CSV Import Stylesheet

         CSV fields:
         Name............................msg_rss_channel.name
         URL.............................msg_rss_channel.url
         Organisation....................pr_contact.pe_id
         Content-Type....................msg_rss_channel.content_type
         Type............................msg_rss_channel.type

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->

    <xsl:template match="/">
        <s3xml>
            <!-- Channels -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="OrgName" select="col[@field='Organisation']/text()"/>
        <xsl:variable name="URL" select="col[@field='URL']/text()"/>

        <resource name="msg_rss_channel">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="url"><xsl:value-of select="$URL"/></data>
            <data field="content_type"><xsl:value-of select="col[@field='Content-Type']"/></data>
            <data field="type"><xsl:value-of select="col[@field='Type']"/></data>
        </resource>

        <xsl:if test="$OrgName!=''">
            <resource name="pr_contact">
                <data field="contact_method" value="RSS"/>
                <data field="value"><xsl:value-of select="$URL"/></data>
                <data field="pe_id">
                    <!-- Name gets converted to ID in pr_import_prep via s3.import_feed -->
                    <xsl:value-of select="$OrgName"/>
                </data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
