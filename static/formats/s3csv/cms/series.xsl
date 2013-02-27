<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         CMS Series - CSV Import Stylesheet

         CSV fields:
         Name.....................Series Name
         Avatar...................Series Avatar
         Location.................Series Location
         Replies..................Series Replies
         Roles....................Series Roles (not yet implemented)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:include href="../../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Series -->
            <xsl:apply-templates select="table/row"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Avatar">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Avatar']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Location">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Location']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="Replies">
            <xsl:call-template name="uppercase">
                <xsl:with-param name="string">
                   <xsl:value-of select="col[@field='Replies']"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:variable>

        <resource name="cms_series">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <xsl:choose>
                <xsl:when test="$Avatar=''">
                    <!-- Use System Default -->
                </xsl:when>
                <xsl:when test="$Avatar='Y'">
                    <data field="avatar" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Avatar='YES'">
                    <data field="avatar" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Avatar='T'">
                    <data field="avatar" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Avatar='TRUE'">
                    <data field="avatar" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Avatar='N'">
                    <data field="avatar" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Avatar='NO'">
                    <data field="avatar" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Avatar='F'">
                    <data field="avatar" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Avatar='FALSE'">
                    <data field="avatar" value="false">False</data>
                </xsl:when>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="$Location=''">
                    <!-- Use System Default -->
                </xsl:when>
                <xsl:when test="$Location='Y'">
                    <data field="location" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Location='YES'">
                    <data field="location" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Location='T'">
                    <data field="location" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Location='TRUE'">
                    <data field="location" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Location='N'">
                    <data field="location" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Location='NO'">
                    <data field="location" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Location='F'">
                    <data field="location" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Location='FALSE'">
                    <data field="location" value="false">False</data>
                </xsl:when>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="$Replies=''">
                    <!-- Use System Default -->
                </xsl:when>
                <xsl:when test="$Replies='Y'">
                    <data field="replies" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Replies='YES'">
                    <data field="replies" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Replies='T'">
                    <data field="replies" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Replies='TRUE'">
                    <data field="replies" value="true">True</data>
                </xsl:when>
                <xsl:when test="$Replies='N'">
                    <data field="replies" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Replies='NO'">
                    <data field="replies" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Replies='F'">
                    <data field="replies" value="false">False</data>
                </xsl:when>
                <xsl:when test="$Replies='FALSE'">
                    <data field="replies" value="false">False</data>
                </xsl:when>
            </xsl:choose>
            <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
