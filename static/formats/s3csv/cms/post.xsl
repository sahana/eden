<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         CMS Post - CSV Import Stylesheet

         CSV fields:
         Series...................Series Name (optional)
         Name.....................Post Name (for menu links)
         Name.....................Post Title (for use in the browser-bar)
         Body.....................Post Body (HTML)
         Module...................Post Module
         Roles....................Post Roles (not yet implemented)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:key name="series" match="row" use="col[@field='Series']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Series -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('series',
                                                                   col[@field='Series'])[1])]">
                <xsl:call-template name="Series"/>
            </xsl:for-each>

            <!-- Posts -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Series" select="col[@field='Series']/text()"/>
        <xsl:variable name="Module" select="col[@field='Module']/text()"/>

        <resource name="cms_post">
            <xsl:if test="$Series!=''">
                <reference field="series_id" resource="cms_series">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="$Series"/>
                    </xsl:attribute>
                </reference>
            </xsl:if>
            <xsl:if test="$Module!=''">
                <data field="module"><xsl:value-of select="$Module"/></data>
            </xsl:if>
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="title"><xsl:value-of select="col[@field='Title']"/></data>
            <data field="body"><xsl:value-of select="col[@field='Body']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Series">
        <xsl:variable name="Series" select="col[@field='Series']/text()"/>

        <resource name="cms_series">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$Series"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$Series"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
