<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Twitter Channels - CSV Import Stylesheet

         CSV fields:
         Name............................msg_twitter_channel.name
         Account.........................msg_twitter_channel.twitter_account

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

        <resource name="msg_twitter_channel">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="twitter_account"><xsl:value-of select="col[@field='Account']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
