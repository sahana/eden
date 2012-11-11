<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- CiviCRM Import Templates

         Copyright (c) 2010-2012 Sahana Software Foundation

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

    -->

    <!-- ****************************************************************** -->
    <xsl:output method="xml"/>

    <xsl:param name="prefix"/>
    <xsl:param name="name"/>
    <xsl:param name="site"/>

    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="ResultSet"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="ResultSet">
        <xsl:variable name="resource" select="concat($prefix, '_', $name)"/>
        <xsl:choose>
            <xsl:when test="$resource='pr_person'">
                <xsl:apply-templates select="Result" mode="pr_person"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="Result" mode="pr_person">
        <xsl:if test="first_name/text()!=''">
            <resource name="pr_person">

                <xsl:attribute name="uuid">
                    <xsl:choose>
                        <xsl:when test="external_identifier/text()!=''">
                            <xsl:value-of select="external_identifier/text()"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="concat('urn:civicrm:contact:',
                                                         $site, '/', id/text())"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>

                <xsl:if test="contact_is_deleted/text()!='0'">
                    <xsl:attribute name="deleted">true</xsl:attribute>
                </xsl:if>

                <data field="first_name"><xsl:value-of select="first_name/text()"/></data>
                <data field="middle_name"><xsl:value-of select="middle_name/text()"/></data>
                <data field="last_name"><xsl:value-of select="last_name/text()"/></data>

                <xsl:apply-templates select="gender_id" mode="pr_person"/>
                <xsl:apply-templates select="birth_date" mode="pr_person"/>

                <xsl:apply-templates select="email" mode="pr_contact"/>

            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="email" mode="pr_contact">

        <xsl:if test="./text()!=''">
            <resource name="pr_contact">
                <data field="contact_method">EMAIL</data>
                <data field="value"><xsl:value-of select="./text()"/></data>
            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="gender_id" mode="pr_person">

        <xsl:if test="./text()!=''">
            <data field="gender">
                <xsl:choose>
                    <xsl:when test="./text()='1'">2</xsl:when>
                    <xsl:when test="./text()='2'">3</xsl:when>
                    <xsl:otherwise>0</xsl:otherwise>
                </xsl:choose>
            </data>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="birth_date" mode="pr_person">
        <xsl:if test="./text()!=''">
            <data field="date_of_birth">
                <xsl:value-of select="./text()"/>
            </data>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="*">
        <!-- catch all -->
    </xsl:template>

</xsl:stylesheet>
