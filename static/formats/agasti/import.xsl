<?xml version="1.0"?>
<xsl:stylesheet
            xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************

         Sahana Agasti-0.6.3 Import Templates for S3XRC (draft)

         Version 0.1 / 2010-08-19 / by nursix

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

    <!-- ****************************************************************** -->
    <xsl:param name="domain"/>

    <xsl:variable name="import_domain">
        <xsl:value-of select="/sahana_data_dump/@instanceid"/>
    </xsl:variable>

    <!-- ****************************************************************** -->
    <xsl:template match="/sahana_data_dump">
        <s3xml>
            <xsl:attribute name="domain">
                <xsl:value-of select="$import_domain"/>
            </xsl:attribute>
            <xsl:apply-templates select="./person_uuid/record"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Person Records (person_uuid) -->
    <xsl:template match="person_uuid/record">
        <xsl:variable name="p_uuid" select="./p_uuid"/>
        <xsl:variable name="uuid" select="concat($import_domain, '/', $p_uuid)"/>
        <resource name="pr_person">
            <!-- UUID -->
            <xsl:attribute name="uuid">
                <xsl:value-of select="$uuid"/>
            </xsl:attribute>
            <!-- Name -->
            <xsl:choose>
                <xsl:when test="./family_name!='null'">
                    <data field="first_name">
                        <xsl:value-of select="substring-before(./full_name, concat(' ', ./family_name))"/>
                    </data>
                    <data field="last_name">
                        <xsl:value-of select="./family_name"/>
                    </data>
                </xsl:when>
                <xsl:otherwise>
                    <data field="first_name">
                        <xsl:value-of select="./full_name"/>
                    </data>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:if test="./l10n_name!='null'">
                <data field="local_name">
                    <xsl:value-of select="./l10n_name"/>
                </data>
            </xsl:if>
            <!-- Other details -->
            <xsl:apply-templates select="/sahana_data_dump/person_details/record[./p_uuid/text()=$p_uuid]"/>
            <xsl:apply-templates select="/sahana_data_dump/person_status/record[./p_uuid/text()=$p_uuid]"/>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Person Details -->
    <xsl:template match="person_details/record">
        <xsl:if test="./birth_date!='null'">
            <data field="date_of_birth">
                <xsl:value-of select="./birth_date"/>
            </data>
        </xsl:if>
        <xsl:if test="./opt_gender='mal'">
            <data field="gender" value="1">male</data>
        </xsl:if>
        <xsl:if test="./opt_gender='fem'">
            <data field="gender" value="2">female</data>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Person Status -->
    <xsl:template match="person_status/record">
        <xsl:if test="./opt_status='mis'">
            <data field="missing" value="True"/>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
