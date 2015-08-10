<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         RSS Channels - CSV Import Stylesheet

         CSV fields:
         Name............................msg_rss_channel.name
         URL.............................msg_rss_channel.url

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

        <resource name="msg_rss_channel">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="url"><xsl:value-of select="col[@field='URL']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
