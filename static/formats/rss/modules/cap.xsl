<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ****************************************************************** -->
    <!-- CAP -->

    <!-- cap_info -->
    <!-- @ToDo: Handle multiple info -->
    <xsl:template match="resource[@name='cap_alert']" mode="contents">
        <!-- referenced template from s3xml -->
        <xsl:if test="./data[@field='is_template' and @value='false']">
            <item>
                <title>
                    <xsl:value-of select="./resource[@name='cap_info']/data[@field='headline']/text()"/>
                </title>
                <description>
                    <xsl:if test="./resource[@name='cap_area']/data[@field='name']/text()">
                        &lt;strong&gt;Alert Location: &lt;/strong&gt;<xsl:value-of select="./resource[@name='cap_area']/data[@field='name']/text()"/>
                    </xsl:if>
                    &lt;br /&gt;
                    <xsl:if test="./resource[@name='cap_info']/data[@field='description']/text()">
                        &lt;strong&gt;Alert Description: &lt;/strong&gt;<xsl:value-of select="./resource[@name='cap_info']/data[@field='description']/text()"/>
                    </xsl:if>
                    &lt;br /&gt;
                    <xsl:if test="./resource[@name='cap_info']/data[@field='sender_name']/text()">
                        &lt;strong&gt;Issued By: &lt;/strong&gt;<xsl:value-of select="./resource[@name='cap_info']/data[@field='sender_name']/text()"/>
                    </xsl:if>                
                </description>
                <link>
                    <!--alert-id substring after last character "/" --> 
                    <xsl:variable name="alert-id">
                        <xsl:call-template name="substring-after-last">
                            <xsl:with-param name="string" select="./@url" />
                            <xsl:with-param name="delimiter" select="'/'" />
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:choose>
                        <xsl:when test="data[@field='scope'] = 'Public'">
                            <xsl:value-of select="concat(../@url,'/cap/public/', $alert-id, '.cap')"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="concat(../@url,'/cap/alert/', $alert-id, '.cap')"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </link>
                <pubDate>
                    <xsl:call-template name="format_datetime">
                        <xsl:with-param name="iso_datetime" select="./data[@field='sent']/@value"/>
                    </xsl:call-template>
                </pubDate>
                <category>
                    <xsl:value-of select="./resource[@name='cap_info']/data[@field='category']/text()"/>
                </category>
                <author>
                    <xsl:value-of select="@owned_by_user"/>
                </author>
            </item>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="substring-after-last">
        <xsl:param name="string"/>
        <xsl:param name="delimiter"/>
        <xsl:choose>
            <xsl:when test="contains($string, $delimiter)">
                <xsl:call-template name="substring-after-last">
                    <xsl:with-param name="string"
                        select="substring-after($string, $delimiter)"/>
                    <xsl:with-param name="delimiter" select="$delimiter"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of
                    select="$string"/>
                </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="format_datetime">

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
        <xsl:variable name="time">
            <xsl:choose>
                <xsl:when test="contains($iso_datetime, 'Z')">
                    <xsl:value-of select="substring-before(substring-after($iso_datetime, 'T'), 'Z')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="substring-after($iso_datetime, 'T')"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:value-of select="concat($day, ' ', $month_name, ' ', $year, ' ', $time, ' GMT')"/>
    </xsl:template>

</xsl:stylesheet>
