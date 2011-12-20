<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:atom="http://www.w3.org/2005/Atom"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:tc="http://schemas.google.com/tablecast/2010">

    <!-- **********************************************************************

         TableCast 0.1 Export Stylesheet / by nursix

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

        @todo: automatically report persons missing if no explicit found-note?

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../xml/commons.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:param name="domain"/>
    <xsl:param name="base_url"/>
    <xsl:param name="utcnow"/>
    <xsl:param name="prefix"/>
    <xsl:param name="name"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <xsl:apply-templates select="./s3xml"/>
    </xsl:template>

    <xsl:template match="s3xml">
        <atom:feed>
            <atom:id>
                <xsl:value-of select="concat('tag:', $domain, ',', substring-before($utcnow, '-'), ':', $prefix, '_', $name)"/>
            </atom:id>
            <atom:updated>
                <xsl:value-of select="$utcnow"/>
            </atom:updated>
            <xsl:apply-templates select=".//resource"/>
        </atom:feed>
    </xsl:template>

    <xsl:template match="resource">
        <xsl:variable name="authority">
            <xsl:choose>
                <xsl:when test="starts-with(@uuid, 'urn:uuid:')">
                    <xsl:text>eden.sahanafoundation.org</xsl:text>
                </xsl:when>
                <xsl:when test="contains(@uuid, '/')">
                    <xsl:value-of select="substring-before(@uuid, '/')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$domain"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="uid">
            <xsl:choose>
                <xsl:when test="starts-with(@uuid, 'urn:')">
                    <xsl:value-of select="translate(substring-after(@uuid, 'urn:'), ':', '/')"/>
                </xsl:when>
                <xsl:when test="contains(@uuid, '/')">
                    <xsl:value-of select="substring-after(@uuid, '/')"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="@uuid"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="entry_id">
            <xsl:value-of select="concat('tag:', $authority, ',', substring-before($utcnow, '-'), ':', $uid)"/>
        </xsl:variable>
        <xsl:variable name="record_id">
            <xsl:value-of select="concat('tag:', $authority, ',', substring-before($utcnow, '-'), ':', @name, '/', $uid)"/>
        </xsl:variable>
        <atom:entry>
            <atom:id>
                <xsl:value-of select="$entry_id"/>
            </atom:id>
            <atom:title>
                <xsl:value-of select="concat(@name, '/', @uuid)"/>
            </atom:title>
            <atom:updated>
                <xsl:value-of select="@modified_on"/>
            </atom:updated>
            <atom:link>
                <xsl:value-of select="@url"/>
            </atom:link>
            <atom:content type="application/tablecast+xml">
                <tc:edit>
                    <xsl:attribute name="record">
                        <xsl:value-of select="$record_id"/>
                    </xsl:attribute>
                    <xsl:attribute name="author">
                        <xsl:value-of select="concat('mailto:', @modified_by)"/>
                    </xsl:attribute>
                    <xsl:attribute name="effective">
                        <xsl:value-of select="@modified_on"/>
                    </xsl:attribute>
                    <xsl:attribute name="type">
                        <xsl:text>{http://schemas.google.com/tablecast/2010}row</xsl:text>
                    </xsl:attribute>
                    <tc:row>
                        <xsl:apply-templates select="data|reference"/>
                    </tc:row>
                </tc:edit>
            </atom:content>
        </atom:entry>
    </xsl:template>

    <xsl:template match="data">
        <tc:field>
            <xsl:attribute name="name">
                <xsl:value-of select="@field"/>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="@value">
                    <xsl:value-of select="@value"/>
                </xsl:when>
                <xsl:when test="./text()!=''">
                    <xsl:text>"</xsl:text>
                    <xsl:value-of select="./text()"/>
                    <xsl:text>"</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>null</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </tc:field>
    </xsl:template>

    <xsl:template match="reference">
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
