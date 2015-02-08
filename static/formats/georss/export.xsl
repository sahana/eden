<xsl:stylesheet version="1.0"
  xmlns="http://www.w3.org/2005/Atom"
  xmlns:georss="http://www.georss.org/georss"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- **********************************************************************

         GeoRSS Export Templates for S3XRC

         Copyright (c) 2011 Sahana Software Foundation

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
    <xsl:output method="xml" indent="yes"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <xsl:apply-templates select="s3xml"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="/s3xml">
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:georss="http://www.georss.org/georss">
            <title>Sahana Eden Locations</title>
            <link href="{@url}"/>
            <xsl:apply-templates select=".//resource[@name='gis_location']"/>
        </feed>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='gis_location']">
        <xsl:variable name="uid">
            <xsl:value-of select="@uuid"/>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="//reference[@resource='gis_location' and @uuid=$uid]">
                <xsl:for-each select="//reference[@resource='gis_location' and @uuid=$uid]">
                    <xsl:apply-templates select=".."/>
                </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
                <entry>
                    <title><xsl:value-of select="data[@field='name']"/></title>
                    <link href="{@url}"/>
                    <id><xsl:value-of select="$uid"/></id>
                    <georss:point>
                        <xsl:value-of select="data[@field='lat']"/>
                        <xsl:text> </xsl:text>
                        <xsl:value-of select="data[@field='lon']"/>
                    </georss:point>
                </entry>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource">
        <xsl:if test="reference[@field='location_id']">
            <entry>
                <title><xsl:value-of select="data[@field='name']"/></title>
                <link href="{@url}"/>
                <id><xsl:value-of select="@uuid"/></id>
                <georss:point>
                    <xsl:value-of select="reference[@field='location_id']/@lat"/>
                    <xsl:text> </xsl:text>
                    <xsl:value-of select="reference[@field='location_id']/@lon"/>
                </georss:point>
            </entry>
        </xsl:if>
    </xsl:template>

</xsl:stylesheet>
