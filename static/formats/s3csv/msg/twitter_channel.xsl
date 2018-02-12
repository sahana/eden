<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Twitter Channels - CSV Import Stylesheet

         CSV fields:
         Name............................msg_twitter_channel.name
         Account.........................msg_twitter_channel.twitter_account
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
        <xsl:variable name="Enabled" select="col[@field='Enabled']/text()"/>

        <resource name="msg_twitter_channel">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="twitter_account"><xsl:value-of select="col[@field='Account']"/></data>
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

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
