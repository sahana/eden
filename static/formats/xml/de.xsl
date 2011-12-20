<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:de="urn:oasis:names:tc:emergency:EDXL:DE:1.0"
    xmlns:xpil="urn:oasis:names:tc:ciq:xpil:3"
    xmlns:xnl="urn:oasis:names:tc:cqi:xnl:3"
    xmlns:xal="urn:oasis:names:tc:ciq:xal:3">

    <!-- **********************************************************************

         Simple EDXL-DE Envelope Template (supports S3XML.envelope)

         Version 0.1 / 2011-11-20 / Dominic König <dominic[at]aidiq[dot]com>

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
    <xsl:output method="xml"/>

    <xsl:param name="distributionID"/>
    <xsl:param name="senderID"/>
    <xsl:param name="dateTimeSent"/>
    <xsl:param name="distributionStatus"/>
    <xsl:param name="distributionType"/>
    <xsl:param name="combinedConfidentiality"/>
    <xsl:param name="contentDescription"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <xsl:call-template name="EDXLDistribution"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="EDXLDistribution">
        <xsl:param name="template"/>
        <de:EDXLDistribution>
            <de:distributionID><xsl:value-of select="$distributionID"/></de:distributionID>
            <de:senderID><xsl:value-of select="$senderID"/></de:senderID>
            <de:dateTimeSent><xsl:value-of select="$dateTimeSent"/></de:dateTimeSent>
            <de:distributionStatus><xsl:value-of select="$distributionStatus"/></de:distributionStatus>
            <de:distributionType><xsl:value-of select="$distributionType"/></de:distributionType>
            <xsl:choose>
                <xsl:when test="$template='true'">
                    <xsl:call-template name="contentObject">
                        <xsl:with-param name="template" select="$template"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:when test="local-name(./*[1])='contents'">
                    <xsl:apply-templates select="contents/object"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="contentObject">
                        <xsl:with-param name="description" select="$contentDescription"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </de:EDXLDistribution>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="object">
        <xsl:variable name="description">
            <xsl:choose>
                <xsl:when test="local-name(./*[1])='description'">
                    <xsl:value-of select="description[1]/text()"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$contentDescription"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:call-template name="contentObject">
            <xsl:with-param name="description" select="$description"/>
        </xsl:call-template>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="contentObject">
        <xsl:param name="template"/>
        <xsl:param name="description"/>
        <de:contentObject>
            <de:contentDescription><xsl:value-of select="$description"/></de:contentDescription>
            <de:embeddedXMLContent>
                <xsl:choose>
                    <xsl:when test="$template='true'">
                        <xsl:apply-templates select="//s3xml"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:copy-of select="./*[local-name()!='description'][1]"/>
                    </xsl:otherwise>
                </xsl:choose>
            </de:embeddedXMLContent>
        </de:contentObject>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
