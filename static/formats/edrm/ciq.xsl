<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns="urn:oasis:names:tc:emergency:EDXL:DE:1.0"
    xmlns:rm="urn:oasis:names:tc:emergency:EDXL:RM:1.0:msg"
    xmlns:xpil="urn:oasis:names:tc:ciq:xpil:3"
    xmlns:xnl="urn:oasis:names:tc:cqi:xnl:3"
    xmlns:xal="urn:oasis:names:tc:ciq:xal:3"
    xmlns:s3="urn:sahana:eden:s3">

    <!-- **********************************************************************

         CIQ Common Templates

         Version 0.1 / 2011-08-09 / Dominic König <dominic[at]aidiq[dot]com>

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
    <xsl:template match="xal:Address" mode="reference">
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="xal:Country" mode="reference">
        <xsl:param name="field"/>
        <xsl:variable name="uuid" select="@s3:uuid"/>
        <reference resource="gis_location">
            <xsl:attribute name="field">
                <xsl:value-of select="$field"/>
            </xsl:attribute>
            <xsl:attribute name="uuid">
                <xsl:choose>
                    <xsl:when test="$uuid">
                        <xsl:value-of select="$uuid"/>
                    </xsl:when>
                    <xsl:when test="xal:Identifier[1]/text()">
                        <xsl:value-of select="concat('urn:iso:std:iso:3166:-1:code:',
                                                     xal:Identifier[1]/text())"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:attribute>
        </reference>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="xal:AdministrativeArea[@xal:Type='state']" mode="reference">
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="xal:Locality[@xal:Type='city']" mode="reference">
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="xal:Locality[@xal:Type='neighborhood']" mode="reference">
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="xal:Thoroughfare" mode="reference">
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="xal:Premises" mode="reference">
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- ****************************************************************** -->
    <xsl:template match="xal:Address" mode="record">
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="xal:Country" mode="record">
        <!-- Do only import if no UUID -->
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="xal:AdministrativeArea[@xal:Type='state']" mode="record">
        <!-- Do only import if no UUID -->
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="xal:Locality[@xal:Type='city']" mode="record">
        <!-- Do only import if no UUID -->
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="xal:Locality[@xal:Type='neighborhood']" mode="record">
        <!-- Do only import if no UUID -->
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="xal:Thoroughfare" mode="record">
        <!-- Do only import if no UUID -->
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="xal:Premises" mode="record">
        <!-- Do only import if no UUID -->
    </xsl:template>

    <!-- ****************************************************************** -->
<!--                  <xal:Address>
                    <xal:Premises>
                      <xal:Identifier>urn:uuid:614242a6-7e37-40dc-bdc6-a7106d54faa8</xal:Identifier>
                      <xal:NameElement>Neal Office</xal:NameElement>
                    </xal:Premises>
                    <xal:Locality xal:Type="neighborhood" s3:uuid="urn:uuid:0b014b10-c790-475b-9f83-24fc4e27eec0">
                      <xal:Name>Warwick</xal:Name>
                    </xal:Locality>
                    <xal:AdministrativeArea xal:Type="state" s3:uuid="urn:uuid:59cd761e-8a65-4e87-bd59-a3c79cfdea93">
                      <xal:NameElement>Co. Longford</xal:NameElement>
                    </xal:AdministrativeArea>
                    <xal:Country s3:uuid="www.sahanafoundation.org/COUNTRY-">
                      <xal:Identifier/>
                    </xal:Country>
                  </xal:Address>-->
</xsl:stylesheet>
