<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         RSS Channels - CSV Import Stylesheet

         CSV fields:
         Name............................msg_rss_channel.name
         URL.............................msg_rss_channel.url
         Organisation....................pr_contact.pe_id
         Content-Type Override...........msg_rss_channel.content_type
         Type............................msg_rss_channel.type
         Enabled.........................msg_rss_channel.enabled (defaults to True)

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
        <xsl:variable name="Enabled" select="col[@field='Enabled']/text()"/>

        <resource name="msg_rss_channel">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="url"><xsl:value-of select="$URL"/></data>

            <!-- Feed-parser to override content-type? -->
            <xsl:variable name="ContentTypeOverride" select="col[@field='Content-Type Override']/text()"/>
            <data field="content-type">
                <xsl:attribute name="value">
                    <xsl:choose>
                        <xsl:when test="$ContentTypeOverride='true'">
                            <xsl:value-of select="'true'"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="'false'"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
            </data>

            <data field="type"><xsl:value-of select="col[@field='Type']"/></data>
            <xsl:choose>
                <xsl:when test="$Enabled='Y'">
                    <data field="enabled" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Enabled='YES'">
                    <data field="enabled" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Enabled='T'">
                    <data field="enabled" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Enabled='TRUE'">
                    <data field="enabled" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Enabled='N'">
                    <data field="enabled" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Enabled='NO'">
                    <data field="enabled" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Enabled='F'">
                    <data field="enabled" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Enabled='FALSE'">
                    <data field="enabled" value="false">False</data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Default to explicit True to have onaccept enable the channel -->
                    <data field="enabled" value="true">True</data>
                </xsl:otherwise>
            </xsl:choose>
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
