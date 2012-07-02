<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ******************************************************************
         Common templates

         include into other stylesheets with:
            <xsl:include href="../xml/commons.xsl"/>

         Copyright (c) 2010-12 Sahana Software Foundation

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
    <!-- Newline variable: use this to insert a newline character into
         strings -->

    <xsl:variable name="newline"><xsl:text>
</xsl:text></xsl:variable>

    <!-- ****************************************************************** -->
    <!-- Convert ISO8601 datetime YYYY-MM-DDTHH:mm:ssZ into web2py default
         YYYY-MM-DD hh:mm:ss

         @param datetime: the datetime string
    -->

    <xsl:template name="iso2datetime">
        <xsl:param name="datetime"/>
        <xsl:variable name="date" select="substring-before($datetime, 'T')"/>
        <xsl:variable name="time" select="substring-after($datetime, 'T')"/>
        <xsl:choose>
            <xsl:when test="contains($time, '.')">
                <xsl:value-of select="concat($date, ' ', substring-before($time, '.'))"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="concat($date, ' ', $time)"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Convert web2py default datetime format YYYY-MM-DD hh:mm:ss
         into ISO8601 YYYY-MM-DDTHH:mm:ss format

         @param datetime: the datetime string
    -->

    <xsl:template name="datetime2iso">
        <xsl:param name="datetime"/>
        <xsl:value-of select="concat(substring-before($datetime, ' '), 'T', substring-after($datetime, ' '))"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Convert a string to uppercase

         @param string: the string
    -->

    <xsl:template name="uppercase">

        <xsl:param name="string"/>
        <xsl:value-of select="translate($string,
            'abcdefghijklmnopqrstuvwxyzáéíóúàèìòùäöüåâêîôûãẽĩõũø',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÀÈÌÒÙÄÖÜÅÂÊÎÔÛÃẼĨÕŨØ')"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Convert a string to lowercase

         @param string: the string
    -->
    <xsl:template name="lowercase">

        <xsl:param name="string"/>
        <xsl:value-of select="translate($string,
            'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÀÈÌÒÙÄÖÜÅÂÊÎÔÛÃẼĨÕŨØ',
            'abcdefghijklmnopqrstuvwxyzáéíóúàèìòùäöüåâêîôûãẽĩõũø')"/>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="left-trim">
        <xsl:param name="s" />
        <xsl:choose>
            <xsl:when test="substring($s, 1, 1) = ''">
              <xsl:value-of select="$s"/>
            </xsl:when>
            <xsl:when test="normalize-space(substring($s, 1, 1)) = ''">
              <xsl:call-template name="left-trim">
                <xsl:with-param name="s" select="substring($s, 2)" />
              </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="$s" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="right-trim">
        <xsl:param name="s" />
        <xsl:choose>
            <xsl:when test="substring($s, 1, 1) = ''">
              <xsl:value-of select="$s"/>
            </xsl:when>
            <xsl:when test="normalize-space(substring($s, string-length($s))) = ''">
              <xsl:call-template name="right-trim">
                <xsl:with-param name="s" select="substring($s, 1, string-length($s) - 1)" />
              </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="$s" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- splitList: split a string with a list into items and call a
         template with the name "resource" with each item as parameter
         "item". The "resource" template is to be defined in the calling
         stylesheet.

         @param list: the string containing the list
         @param sep: the list separator
         @param arg: argument to be passed on to the "resource" template
    -->
    <xsl:template name="splitList">

        <xsl:param name="list"/>
        <xsl:param name="listsep" select="','"/>
        <xsl:param name="arg"/>

        <xsl:if test="$listsep">
            <xsl:choose>
                <xsl:when test="contains($list, $listsep)">
                    <xsl:variable name="head">
                        <xsl:value-of select="substring-before($list, $listsep)"/>
                    </xsl:variable>
                    <xsl:variable name="tail">
                        <xsl:value-of select="substring-after($list, $listsep)"/>
                    </xsl:variable>
                    <xsl:call-template name="resource">
                        <xsl:with-param name="item" select="normalize-space($head)"/>
                        <xsl:with-param name="arg" select="$arg"/>
                    </xsl:call-template>
                    <xsl:call-template name="splitList">
                        <xsl:with-param name="list" select="$tail"/>
                        <xsl:with-param name="listsep" select="$listsep"/>
                        <xsl:with-param name="arg" select="$arg"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="normalize-space($list)!=''">
                        <xsl:call-template name="resource">
                            <xsl:with-param name="item" select="normalize-space($list)"/>
                            <xsl:with-param name="arg" select="$arg"/>
                            <xsl:with-param name="last">true</xsl:with-param>
                        </xsl:call-template>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Quote list: split a string with a list into its items and construct
         a new list with the same items quoted

         @param list: a string containing the list
         @param listsep: the list separator in the original list
         @param joinsep: the separator for the quoted list
         @param prefix: prefix for each item in the quoted list
    -->
    <xsl:template name="quoteList">

        <xsl:param name="list"/>
        <xsl:param name="listsep" select="','"/>
        <xsl:param name="joinsep" select="','"/>
        <xsl:param name="prefix" select="''"/>

        <xsl:if test="$listsep">
            <xsl:choose>
                <xsl:when test="contains($list, $listsep)">
                    <xsl:variable name="head">
                        <xsl:value-of select="normalize-space(substring-before($list, $listsep))"/>
                    </xsl:variable>
                    <xsl:variable name="tail">
                        <xsl:value-of select="substring-after($list, $listsep)"/>
                    </xsl:variable>
                    <xsl:choose>
                        <xsl:when test="normalize-space($tail)">
                            <xsl:value-of select="concat('&quot;', $prefix, $head, '&quot;', $joinsep)"/>
                            <xsl:call-template name="quoteList">
                                <xsl:with-param name="list" select="$tail"/>
                                <xsl:with-param name="listsep" select="$listsep"/>
                                <xsl:with-param name="joinsep" select="$joinsep"/>
                                <xsl:with-param name="prefix" select="$prefix"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:if test="$head">
                                <xsl:value-of select="concat('&quot;', $prefix, $head, '&quot;')"/>
                            </xsl:if>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:if test="normalize-space($list)!=''">
                        <xsl:value-of select="concat('&quot;', $prefix, normalize-space($list), '&quot;')"/>
                    </xsl:if>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Resolve Column header

         Helper template to resolve column header variants, using both
         an external labels.xml and the <labels> subtree in the source.

         Parameter column: the standard column label
         Output: a |-delimited string of alternative column labels
    -->

    <xsl:template name="ResolveColumnHeader">

        <xsl:param name="colname"/>
        <xsl:variable name="labels" select="document('labels.xml')//labels"/>
        <xsl:variable name="src" select="//labels/column[@name=$colname]"/>
        <xsl:variable name="map" select="$labels/column[@name=$colname]"/>
        <xsl:value-of select="concat('|', $colname, '|')"/>
        <xsl:for-each select="$src/label">
            <xsl:variable name="label" select="text()"/>
            <xsl:variable name="duplicates" select="preceding-sibling::label[text()=$label]"/>
            <xsl:if test="$label != $colname and not($duplicates)">
                <xsl:value-of select="concat($label, '|')"/>
            </xsl:if>
        </xsl:for-each>
        <xsl:for-each select="$map/label">
            <xsl:variable name="label" select="text()"/>
            <xsl:variable name="srcdup" select="$src/label[text()=$label]"/>
            <xsl:variable name="mapdup" select="preceding-sibling::label[text()=$label]"/>
            <xsl:if test="$label != $colname and not($srcdup) and not ($mapdup)">
                <xsl:value-of select="concat($label, '|')"/>
            </xsl:if>
        </xsl:for-each>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- Get Column Value

         Extracts the value of a column in the current <row> and resolves
         any option label variants, using both an external labels.xml and
         the <labels> subtree in the source.

         Parameter colhdrs: all column header variants as a |-delimited
                            string (as returned from ResolveColumnHeader)
         Output: the column value
    -->

    <xsl:template name="GetColumnValue">

        <xsl:param name="colhdrs"/>
        <xsl:variable name="colname" select="substring-before(substring-after($colhdrs, '|'), '|')"/>
        <xsl:variable name="col" select="col[contains($colhdrs, concat('|', @field, '|'))][1]"/>
        <xsl:variable name="srcmap" select="//labels/column[@name=$colname]"/>
        <xsl:variable name="lblmap" select="document('labels.xml')//labels/column[@name=$colname]"/>
        <xsl:variable name="label" select="$col/text()"/>
        <xsl:variable name="alt1" select="$srcmap/option[@name=$label or ./label/text()=$label]"/>
        <xsl:variable name="alt2" select="$lblmap/option[@name=$label or ./label/text()=$label]"/>
        <xsl:choose>
            <xsl:when test="$alt1">
                <xsl:value-of select="$alt1[1]/@value"/>
            </xsl:when>
            <xsl:when test="$alt2">
                <xsl:value-of select="$alt2[1]/@value"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$label"/>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>
    
    <!-- ****************************************************************** -->
    <!-- substringAfterLast

         Parameter input: the input string ( e.g. a URL )
         Parameter sep: the separator ( e.g. '/')
         Output: the substring after the last occurrence of the separator
    -->

    <xsl:template name="substringAfterLast">

        <xsl:param name="input"/>
        <xsl:param name="sep"/>
        <xsl:choose>
            <xsl:when test="contains($input, $sep)">
                <xsl:call-template name="substringAfterLast">
                    <xsl:with-param name="input" select="substring-after($input, $sep)"/>
                    <xsl:with-param name="sep" select="$sep"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$input"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
