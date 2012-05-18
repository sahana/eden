<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:pfif="http://zesty.ca/pfif/1.2">

    <!-- **********************************************************************

         PFIF 1.2 Export Templates for Sahana-Eden

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
    <xsl:include href="../xml/commons.xsl"/>
    <xsl:include href="../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:param name="domain"/>
    <xsl:param name="base_url"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <xsl:apply-templates select="./s3xml"/>
    </xsl:template>

    <xsl:template match="/s3xml">
        <pfif:pfif>
            <xsl:apply-templates select="./resource[@name='pr_person' and not(@ref)]"/>
        </pfif:pfif>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='pr_person']">
        <pfif:person>

            <!-- Record ID -->
            <pfif:person_record_id>
                <xsl:value-of select="concat($domain, '/', @uuid)" />
            </pfif:person_record_id>

            <!-- Source Information -->
            <pfif:source_name>
                <xsl:value-of select="/s3xml/@domain"/>
            </pfif:source_name>
            <pfif:source_date>
                <xsl:value-of select="@created_on" />
            </pfif:source_date>
            <pfif:source_url>
                <xsl:value-of select="@url"/>
            </pfif:source_url>

            <!-- Entry date and Author -->
            <pfif:entry_date>
                <xsl:value-of select="@modified_on" />
            </pfif:entry_date>
            <pfif:author_email>
                <xsl:value-of select="@modified_by" />
            </pfif:author_email>

            <!-- Person names -->
            <pfif:first_name>
                <xsl:value-of select="./data[@field='first_name']/text()" />
            </pfif:first_name>
            <pfif:last_name>
                <xsl:value-of select="./data[@field='last_name']/text()" />
            </pfif:last_name>

            <!-- Sex, Date of Birth -->
            <xsl:choose>
                <xsl:when test="./data[@field='gender']/@value='2'">
                    <pfif:sex>female</pfif:sex>
                </xsl:when>
                <xsl:when test="./data[@field='gender']/@value='3'">
                    <pfif:sex>male</pfif:sex>
                </xsl:when>
            </xsl:choose>
            <xsl:if test="./data[@field='date_of_birth']">
                <pfif:date_of_birth>
                    <xsl:value-of select="./data[@field='date_of_birth']"/>
                </pfif:date_of_birth>
            </xsl:if>

            <!-- Image -->
            <xsl:apply-templates select="./resource[@name='pr_image'][1]"/>

            <!-- Address -->
            <xsl:apply-templates select="./resource[@name='pr_address' and
                                         ./data[@field='type']/@value=1][1]" />

            <!-- Note -->
            <xsl:apply-templates select="./resource[@name='pr_note']"/>

        </pfif:person>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='pr_image']">
        <xsl:variable name="url">
            <xsl:value-of select="substring-before(substring-after(./data[@field='url']/@value, '&quot;'), '&quot;')"/>
        </xsl:variable>

        <xsl:if test="$url">
            <pfif:photo_url>
                <xsl:value-of select="$url"/>
            </pfif:photo_url>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='pr_note']">
        <pfif:note>
            <pfif:note_record_id>
                <xsl:value-of select="concat($domain, '/', @uuid)" />
            </pfif:note_record_id>
            <pfif:person_record_id>
                <xsl:value-of select="concat($domain, '/', ../@uuid)" />
            </pfif:person_record_id>

            <pfif:entry_date>
                <xsl:value-of select="@modified_on"/>
            </pfif:entry_date>
            <pfif:author_email>
                <xsl:value-of select="@modified_by"/>
            </pfif:author_email>

            <pfif:source_date>
                <xsl:value-of select="./data[@field='timestmp']"/>
            </pfif:source_date>

            <pfif:status>
                <xsl:choose>
                    <xsl:when test="./data[@field='status']/@value=1">
                        <xsl:text>believed_missing</xsl:text>
                    </xsl:when>
                    <xsl:when test="./data[@field='status']/@value=3">
                        <xsl:text>believed_dead</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>believed_alive</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </pfif:status>

            <pfif:found>
                <xsl:choose>
                    <xsl:when test="./data[@field='status']/@value=2">
                        <xsl:text>true</xsl:text>
                    </xsl:when>
                    <xsl:when test="./data[@field='presence_condition']/@value=11">
                        <xsl:text>true</xsl:text>
                    </xsl:when>
                    <xsl:when test="./data[@field='presence_condition']/@value=12">
                        <xsl:text>true</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:text>false</xsl:text>
                    </xsl:otherwise>
                </xsl:choose>
            </pfif:found>

            <!-- todo: replace by sit_presence -->
            <xsl:if test="./data[@field='location']/text()">
                <pfif:last_known_location>
                    <xsl:value-of select="./data[@field='location']/text()"/>
                </pfif:last_known_location>
            </xsl:if>
            <pfif:text>
                <xsl:value-of select="./data[@field='note_text']/text()"/>
            </pfif:text>
        </pfif:note>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="resource[@name='pr_person']/resource[@name='pr_address']">
        <pfif:home_street>
            <xsl:value-of select="./data[@field='address']/text()"/>
        </pfif:home_street>

        <!-- Neighborhood not supported
        <pfif:home_neighborhood>
        </pfif:home_neighborhood>
        -->

        <pfif:home_city>
            <xsl:value-of select="./data[@field='L3']/text()"/>
        </pfif:home_city>
        <pfif:home_state>
            <xsl:value-of select="./data[@field='L1']/text()"/>
        </pfif:home_state>
        <pfif:home_postal_code>
            <xsl:value-of select="./data[@field='postcode']/text()"/>
        </pfif:home_postal_code>

        <!-- ISO 3166-1 Country Codes -->
        <pfif:home_country>
            <xsl:call-template name="countryname2iso">
                <xsl:with-param name="country" select="./data[@field='L0']/text()"/>
            </xsl:call-template>
        </pfif:home_country>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
