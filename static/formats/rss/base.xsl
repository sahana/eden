<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         RSS Base Templates for S3XRC

         Version 0.1 / 2010-06-17 / by nursix

         Copyright (c) 2010 Sahana Software Foundation

         Permission is hereby granted, free of charge, to any person
         obtaining a copy of this software and associated documentation
         files (the "Software"), to deal in the Software without
         restriction, including without limitation the rights to use,
         copy, modify, merge, publish, distribute, sublicense, and/or sell
         copies of the Software, and to permit persons to whom the
         Software is furnished to do so, subject to the following
         conditions:

         The above copyright notice and this permission notice shall be
         included in all copies or substantial portions of the Software.

         THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
         EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
         OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
         NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
         HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
         WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
         FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
         OTHER DEALINGS IN THE SOFTWARE.

    *********************************************************************** -->
    <xsl:template match="/">
        <xsl:apply-templates select="./s3xml"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="s3xml">
        <xsl:variable name="resource_url">
            <xsl:call-template name="resource_url"/>
        </xsl:variable>
        <rss version="2.0">
            <channel>
                <xsl:call-template name="channel_header">
                    <xsl:with-param name="resource_url" select="$resource_url"/>
                </xsl:call-template>
                <xsl:variable name="target">
                    <xsl:choose>
                        <xsl:when test="$component">
                            <xsl:value-of select="$component"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="concat($prefix, '_', $name)"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:value-of select="$target"/>
                <xsl:apply-templates select=".//resource[@name=$target]" mode="item">
                    <xsl:with-param name="resource_url" select="$resource_url"/>
                </xsl:apply-templates>
            </channel>
        </rss>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource" mode="item">

        <xsl:param name="resource_url"/>
        <xsl:variable name="resource_name">
            <xsl:call-template name="resource_name"/>
        </xsl:variable>
        <item>
            <link>
                <xsl:value-of select="concat($resource_url, '?', $resource_name, '.uid=', @uuid)"/>
            </link>
            <pubDate>
                <xsl:if test="@modified_on">
                    <xsl:call-template name="rfc_822_datetime">
                        <xsl:with-param name="iso_datetime" select="@modified_on"/>
                    </xsl:call-template>
                </xsl:if>
            </pubDate>
            <xsl:apply-templates select="." mode="contents"/>
        </item>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource" mode="contents">
        <title><xsl:value-of select="@name"/></title>
        <description><xsl:value-of select="@uuid"/></description>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="channel_header">

        <xsl:param name="resource_url"/>
        <title>
            <xsl:value-of select="$title"/>
        </title>
        <link>
            <xsl:value-of select="$resource_url"/>
        </link>
        <description></description>
        <lastBuildDate>
            <xsl:call-template name="rfc_822_datetime">
                <xsl:with-param name="iso_datetime" select="$utcnow"/>
            </xsl:call-template>
        </lastBuildDate>
        <generator>Sahana-Eden</generator>
        <docs>http://blogs.law.harvard.edu/tech/rss</docs>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource_url">
        <xsl:variable name="resource_url"
                      select="concat($base_url, '/', $prefix, '/', $name)"/>
        <xsl:variable name="component_name"
                      select="substring-after($component, '_')"/>
        <xsl:choose>
            <xsl:when test="$id and $component">
                <xsl:value-of select="concat($resource_url, '/', $id, '/', $component_name)"/>
            </xsl:when>
            <xsl:when test="$id">
                <xsl:value-of select="concat($resource_url, '/', $id)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$resource_url"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="resource_name">
        <xsl:choose>
            <xsl:when test="$component">
                <xsl:value-of select="substring-after($component, '_')"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$name"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="rfc_822_datetime">

        <!-- This template expects a datetime string in ISO-format
             YYYY-mm-dd HH:MM:SS and transforms it into a datetime
             compliant to http://asg.web.cmu.edu/rfc/rfc822.html#sec-5 -->

        <xsl:param name="iso_datetime"/>
        <xsl:variable name="year"
                      select="substring($iso_datetime, 1, 4)"/>
        <xsl:variable name="month"
                      select="substring($iso_datetime, 6, 2)"/>
        <xsl:variable name="day"
                      select="substring($iso_datetime, 9, 2)"/>
        <xsl:variable name="month_name">
            <xsl:choose>
                <xsl:when test="$month='01'"><xsl:value-of select="'Jan'"/></xsl:when>
                <xsl:when test="$month='02'"><xsl:value-of select="'Feb'"/></xsl:when>
                <xsl:when test="$month='03'"><xsl:value-of select="'Mar'"/></xsl:when>
                <xsl:when test="$month='04'"><xsl:value-of select="'Apr'"/></xsl:when>
                <xsl:when test="$month='05'"><xsl:value-of select="'May'"/></xsl:when>
                <xsl:when test="$month='06'"><xsl:value-of select="'Jun'"/></xsl:when>
                <xsl:when test="$month='07'"><xsl:value-of select="'Jul'"/></xsl:when>
                <xsl:when test="$month='08'"><xsl:value-of select="'Aug'"/></xsl:when>
                <xsl:when test="$month='09'"><xsl:value-of select="'Sep'"/></xsl:when>
                <xsl:when test="$month='10'"><xsl:value-of select="'Oct'"/></xsl:when>
                <xsl:when test="$month='11'"><xsl:value-of select="'Nov'"/></xsl:when>
                <xsl:when test="$month='12'"><xsl:value-of select="'Dec'"/></xsl:when>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="time"
                      select="substring-before(substring-after($iso_datetime, 'T'), 'Z')"/>
        <xsl:value-of select="concat($day, ' ', $month_name, ' ', $year, ' ', $time, ' GMT')"/>
    </xsl:template>

</xsl:stylesheet>
