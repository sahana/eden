<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:pfif="http://zesty.ca/pfif/1.2">

    <!-- **********************************************************************

         PFIF 1.2 Import Templates

         Version 0.4 / 2011-05-09 / by nursix

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
    <xsl:include href="../xml/countries.xsl"/>

    <!-- ****************************************************************** -->
    <xsl:param name="domain"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <xsl:attribute name="domain">
                <xsl:value-of select="$domain"/>
            </xsl:attribute>
            <xsl:apply-templates select=".//pfif:person"/>
        </s3xml>
    </xsl:template>

    <xsl:template match="text()"/>

    <!-- ****************************************************************** -->
    <!-- pfif:person -->

    <xsl:template match="pfif:person">
        <xsl:if test="./pfif:person_record_id/text()">
            <xsl:variable name="uuid">
                <xsl:value-of select="./pfif:person_record_id/text()"/>
            </xsl:variable>

            <resource name="pr_person">
                <xsl:attribute name="uuid">
                    <xsl:value-of select="$uuid"/>
                </xsl:attribute>
                <xsl:attribute name="modified_on">
                    <xsl:value-of select="./pfif:entry_date/text()"/>
                </xsl:attribute>
                <data field="first_name">
                    <xsl:value-of select="normalize-space(./pfif:first_name/text())"/>
                </data>
                <data field="last_name">
                    <xsl:value-of select="normalize-space(./pfif:last_name/text())"/>
                </data>
                <xsl:if test="normalize-space(./pfif:full_name/text())!=''">
                    <data field="local_name">
                        <xsl:value-of select="normalize-space(./pfif:full_name/text())!=''"/>
                    </data>
                </xsl:if>
                <data field="gender">
                    <xsl:choose>
                        <xsl:when test="./pfif:sex/text()='female'">
                            <xsl:attribute name="value">2</xsl:attribute>
                        </xsl:when>
                        <xsl:when test="./pfif:sex/text()='male'">
                            <xsl:attribute name="value">3</xsl:attribute>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:attribute name="value">1</xsl:attribute>
                        </xsl:otherwise>
                    </xsl:choose>
                </data>
                <xsl:if test="./pfif:date_of_birth/text()">
                    <data field="date_of_birth">
                        <xsl:value-of select="./pfif:date_of_birth/text()"/>
                    </data>
                </xsl:if>

                <!-- Address -->
                <xsl:if test="./pfif:home_city">
                    <resource name="pr_address">
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="concat($uuid, '_address')"/>
                        </xsl:attribute>
                        <data field="type" value="1">Home Address</data>
                        <reference field="location_id" resource="gis_location">
                            <resource name="gis_location">
                                <data field="name">
                                    <xsl:value-of select="./pfif:first_name/text()"/>
                                    <xsl:text> </xsl:text>
                                    <xsl:value-of select="./pfif:last_name/text()"/>
                                </data>
                                <data field="address">
                                    <xsl:value-of select="./pfif:home_street/text()"/>
                                </data>
                                <data field="L3">
                                    <xsl:value-of select="./pfif:home_city/text()"/>
                                </data>
                                <data field="L1">
                                    <xsl:value-of select="./pfif:home_state/text()"/>
                                </data>
                                <data field="L0">
                                    <xsl:call-template name="iso2countryname">
                                        <xsl:with-param name="country" select="./pfif:home_country/text()"/>
                                    </xsl:call-template>
                                </data>
                                <data field="postcode">
                                    <xsl:value-of select="./pfif:home_postal_code/text()"/>
                                </data>
                            </resource>
                        </reference>
                    </resource>
                </xsl:if>

                <!-- PhotoURL: save external URL -->
                <xsl:if test="./pfif:photo_url">
                    <data field="picture">
                        <xsl:attribute name="url">
                            <xsl:value-of select="./pfif:photo_url/@text()"/>
                        </xsl:attribute>
                    </data>
                </xsl:if>

                <!-- Add notes -->
                <xsl:apply-templates select="//pfif:note[pfif:person_record_id=$uuid]"/>

            </resource>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- pfif:note -->

    <xsl:template match="pfif:note">
        <resource name="pr_note">

            <!-- Meta Data -->
            <xsl:attribute name="uuid">
                <xsl:value-of select="./pfif:note_record_id/text()"/>
            </xsl:attribute>
            <xsl:attribute name="modified_on">
                <xsl:value-of select="./pfif:entry_date/text()"/>
            </xsl:attribute>

            <!-- Missing or Found -->
            <xsl:choose>
                <xsl:when test="normalize-space(./pfif:found/text())='true'">
                    <data field="status">
                        <xsl:attribute name="value">2</xsl:attribute>
                    </data>
                </xsl:when>
                <xsl:when test="normalize-space(./pfif:status/text())='believed_missing'">
                    <data field="status">
                        <xsl:attribute name="value">1</xsl:attribute>
                    </data>
                </xsl:when>
                <xsl:when test="normalize-space(./pfif:status/text())='believed_dead'">
                    <data field="status">
                        <xsl:attribute name="value">3</xsl:attribute>
                    </data>
                </xsl:when>
                <xsl:otherwise>
                    <data field="status">
                        <xsl:attribute name="value">9</xsl:attribute>
                    </data>
                </xsl:otherwise>
            </xsl:choose>

            <!-- Date/Time -->
            <data field="timestmp">
                <xsl:value-of select="./pfif:entry_date/text()"/>
            </data>

            <!-- Note text -->
            <data field="note_text">
                <xsl:value-of select="./pfif:text/text()"/>
            </data>
        </resource>
    </xsl:template>

</xsl:stylesheet>
