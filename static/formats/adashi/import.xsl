<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         ADASHI Configuration Import Templates for Sahana Eden

         Copyright (c) 2015-16 Sahana Software Foundation

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

        <s3xml>
            <xsl:choose>
                <xsl:when test="CadStatusConfigOptions">
                    <xsl:apply-templates select="CadStatusConfigOptions"/>
                </xsl:when>
            </xsl:choose>
        </s3xml>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="CadStatusConfigOptions">

        <xsl:apply-templates select="CADStatuses/CadStatus"/>

    </xsl:template>
    <!-- ****************************************************************** -->
    <xsl:template match="CadStatus">

        <resource name="pr_group_status">
            <data field="code">
                <xsl:value-of select="CadDatabaseString/text()"/>
            </data>
            <data field="name">
                <xsl:value-of select="LongDisplayString/text()"/>
            </data>
            <data field="comments">
                <xsl:value-of select="Description/text()"/>
            </data>
        </resource>

    </xsl:template>
    <!-- ****************************************************************** -->

</xsl:stylesheet>
