<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ****************************************************************** -->
    <!-- CAP -->

    <!-- cap_info -->
    <!-- @ToDo: Handle multiple info -->
    <xsl:template match="resource[@name='cap_alert']" mode="contents">
        <!-- filter non-template internal alerts that are approved -->
        <xsl:if test="./data[@field='is_template' and @value='false'] and ./data[@field='external' and @value='false'] and ./data[@field='approved_on']">
            <title>
                <xsl:value-of select="./resource[@name='cap_info']/data[@field='headline']/text()"/>
            </title>
            <description>
                <xsl:if test="./resource[@name='cap_area']/data[@field='name']/text()">
                    <strong>Alert Location: </strong><xsl:value-of select="./resource[@name='cap_area']/data[@field='name']/text()"/>
                </xsl:if>
                <br />
                <xsl:if test="./resource[@name='cap_info']/data[@field='description']/text()">
                    <strong>Alert Description: </strong><xsl:value-of select="./resource[@name='cap_info']/data[@field='description']/text()"/>
                </xsl:if>
                <br />
                <xsl:if test="./resource[@name='cap_info']/data[@field='sender_name']/text()">
                    <strong>Issued By: </strong><xsl:value-of select="./resource[@name='cap_info']/data[@field='sender_name']/text()"/>
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
                <xsl:value-of select="./data[@field='sent']/text()"/>
            </pubDate>
            <category>
                <xsl:value-of select="./resource[@name='cap_info']/data[@field='category']/text()"/>
            </category>
            <author>
                <xsl:value-of select="./resource[@name='cap_info']/data[@field='sender_name']/text()"/>
            </author>
        </xsl:if>
    </xsl:template>

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

</xsl:stylesheet>
