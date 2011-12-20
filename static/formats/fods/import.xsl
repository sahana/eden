<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
    xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0">

    <!-- **********************************************************************

         Simple Import Stylesheet for
         OpenOffice Spreadsheets in flat ODF-XML format (.fods)

         Sheet name = resource name
         First row = attribute/field names
         Other rows = attribute/field values

         References:
            1) Insert another sheet with the entries of the referenced table,
               this sheet must have the same name as the referenced table and
               a column "uuid"
            2) Insert a column in the main sheet with a column title like:
                    reference:<fieldname>:<referenced_table>
                e.g. "reference:organisation_id:org_organisation"
            3) fill in this column with the UUIDs of the respective entries
               in the referenced table

         Components:
            1) Insert another sheet with the entries of the component table,
               this sheet must have a name like:
                   <main-table-name>+<component-table-name>
               e.g. "hms_hospital+hms_hactivity"
            2) Insert a column into the component sheet with a name like:
                   <main-table-name>.<key-field>
               e.g. "hms_hospital.gov_uuid"
               => the key field must be present in the main table
               => the key field must be unique (primary key) in the main table
            3) Fill in this column with the respective values of the key field
               in the parent entry of the main table

         Version 0.1.4 / 2010-09-19 / by nursix

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
    <xsl:template match="/">
        <s3xml>
            <xsl:apply-templates select="//office:spreadsheet"/>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="office:spreadsheet">
        <xsl:apply-templates select="./table:table"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Tables -->
    <xsl:template match="table:table">
        <xsl:if test="not(contains(@table:name, '+'))">
            <xsl:apply-templates select="./table:table-row[position()>1]"/>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Rows -->
    <xsl:template match="table:table-row">
        <resource>
            <xsl:attribute name="name">
                <xsl:choose>
                    <xsl:when test="starts-with(../@table:name, '+')">
                        <xsl:value-of select="substring-after(../@table:name, '+')"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="../@table:name"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            <xsl:attribute name="mci">1</xsl:attribute>
            <xsl:apply-templates select="./table:table-cell" mode="attributes"/>
            <xsl:apply-templates select="./table:table-cell" mode="fields"/>
            <xsl:call-template name="components">
                <xsl:with-param name="row" select="."/>
                <xsl:with-param name="table" select=".."/>
            </xsl:call-template>
        </resource>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Attribute cells -->
    <xsl:template match="table:table-cell" mode="attributes">

        <xsl:variable name="fieldindex" select="position()"/>
        <xsl:variable name="fieldname" select="../../table:table-row[1]/table:table-cell[$fieldindex]/text:p/text()"/>

        <xsl:if test="$fieldname='uuid'">
            <xsl:attribute name="uuid">
                <xsl:value-of select="./text:p/text()"/>
            </xsl:attribute>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Field cells -->
    <xsl:template match="table:table-cell" mode="fields">

        <xsl:variable name="fieldindex" select="position()"/>
        <xsl:variable name="fieldname" select="../../table:table-row[1]/table:table-cell[$fieldindex]/text:p/text()"/>

        <xsl:if test="$fieldname!='uuid'">
            <xsl:choose>

                <!-- resolve references -->
                <xsl:when test="starts-with($fieldname, 'reference:')">
                    <reference>
                        <xsl:attribute name="field">
                            <xsl:value-of select="substring-before(substring-after($fieldname, 'reference:'), ':')"/>
                        </xsl:attribute>
                        <xsl:attribute name="resource">
                            <xsl:value-of select="substring-after(substring-after($fieldname, 'reference:'), ':')"/>
                        </xsl:attribute>
                        <xsl:attribute name="uuid">
                            <xsl:value-of select="./text:p/text()"/>
                        </xsl:attribute>
                    </reference>
                </xsl:when>

                <xsl:when test="contains($fieldname, ':') or contains($fieldname, '.')">
                    <!-- ignore -->
                </xsl:when>

                <!-- data -->
                <xsl:otherwise>
                    <data>
                        <xsl:attribute name="field">
                            <xsl:value-of select="$fieldname"/>
                        </xsl:attribute>
                        <xsl:value-of select="./text:p/text()"/>
                    </data>
                </xsl:otherwise>

            </xsl:choose>
        </xsl:if>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="components">
        <xsl:param name="table"/>
        <xsl:param name="row"/>

        <xsl:variable name="tablename" select="$table/@table:name"/>
        <xsl:variable name="prefix" select="substring-before($tablename, '_')"/>

        <xsl:for-each select="$table/../table:table[starts-with(@table:name, concat($tablename, '+'))]">
            <xsl:variable name="componentname" select="substring-after(@table:name, '+')"/>
            <xsl:variable name="join" select="./table:table-row[1]/table:table-cell[starts-with(text:p/text(), $tablename)][1]/text:p/text()"/>
            <xsl:variable name="join-position">
                <xsl:for-each select="./table:table-row[1]/table:table-cell">
                    <xsl:if test="text:p/text()=$join">
                        <xsl:value-of select="position()"/>
                    </xsl:if>
                </xsl:for-each>
            </xsl:variable>
            <xsl:variable name="from-position">
                <xsl:for-each select="$table/table:table-row[1]/table:table-cell">
                    <xsl:if test="text:p/text()=substring-after($join, '.')">
                        <xsl:value-of select="position()"/>
                    </xsl:if>
                </xsl:for-each>
            </xsl:variable>
            <xsl:if test="$join-position and $from-position">
                <xsl:for-each select="./table:table-row[position()>1 and table:table-cell[$join-position]/text:p/text()=$row/table:table-cell[$from-position]/text:p/text()]">
                    <resource>
                        <xsl:attribute name="name">
                            <xsl:value-of select="$componentname"/>
                        </xsl:attribute>
                        <xsl:apply-templates select="./table:table-cell" mode="attributes"/>
                        <xsl:apply-templates select="./table:table-cell" mode="fields" />
                    </resource>
                </xsl:for-each>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
