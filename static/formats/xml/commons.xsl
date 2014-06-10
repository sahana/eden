<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- ******************************************************************
         Common templates

         include into other stylesheets with:
            <xsl:include href="../xml/commons.xsl"/>

         Copyright (c) 2010-14 Sahana Software Foundation

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
                     to allow differentiation
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
    <!-- splitMultiList: split a hierarchical set of string with lists into
         items and call a template with the name "multiResource" with each item
         as parameter "item". The "multiResource" template is to be defined in
         the calling stylesheet.

         @param list: the string containing the list
         @param list2: the string containing the list
         @param list3: the string containing the list
         @param sep: the primary list separator
         @param sep2: the secondary list separator
         @param sep3: the tertiary list separator
         @param arg: argument to be passed on to the "multiResource" template
                     to allow differentiation
    -->
    <xsl:template name="splitMultiList">

        <xsl:param name="arg"/>
        <xsl:param name="list"/>
        <xsl:param name="list2"/>
        <xsl:param name="list3"/>
        <xsl:param name="listsep" select="','"/>
        <xsl:param name="listsep2" select="';'"/>
        <xsl:param name="listsep3" select="':'"/>

        <xsl:choose>
            <!-- Unwrap level 1 -->
            <xsl:when test="contains($list, $listsep)">
                <xsl:variable name="head">
                    <xsl:value-of select="substring-before($list, $listsep)"/>
                </xsl:variable>
                <xsl:variable name="head2">
                    <xsl:choose>
                        <xsl:when test="contains($list2, $listsep2)">
                            <xsl:value-of select="substring-before($list2, $listsep2)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$list2"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="head3">
                    <xsl:choose>
                        <xsl:when test="contains($list3, $listsep3)">
                            <xsl:value-of select="substring-before($list3, $listsep3)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$list3"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="tail">
                    <xsl:value-of select="substring-after($list, $listsep)"/>
                </xsl:variable>
                <xsl:variable name="tail2">
                    <xsl:choose>
                        <xsl:when test="contains($list2, $listsep2)">
                            <xsl:value-of select="substring-after($list2, $listsep2)"/>
                        </xsl:when>
                        <!-- Otherwise Blank -->
                    </xsl:choose>
                </xsl:variable>
                <xsl:variable name="tail3">
                    <xsl:choose>
                        <xsl:when test="contains($list3, $listsep3)">
                            <xsl:value-of select="substring-after($list3, $listsep3)"/>
                        </xsl:when>
                        <!-- Otherwise Blank -->
                    </xsl:choose>
                </xsl:variable>
                <xsl:call-template name="splitMultiList">
                    <xsl:with-param name="arg" select="$arg"/>
                    <xsl:with-param name="list" select="$head"/>
                    <xsl:with-param name="list2" select="$head2"/>
                    <xsl:with-param name="list3" select="$head3"/>
                    <xsl:with-param name="listsep" select="$listsep"/>
                    <xsl:with-param name="listsep2" select="$listsep2"/>
                    <xsl:with-param name="listsep3" select="$listsep3"/>
                </xsl:call-template>
                <xsl:call-template name="splitMultiList">
                    <xsl:with-param name="arg" select="$arg"/>
                    <xsl:with-param name="list" select="$tail"/>
                    <xsl:with-param name="list2" select="$tail2"/>
                    <xsl:with-param name="list3" select="$tail3"/>
                    <xsl:with-param name="listsep" select="$listsep"/>
                    <xsl:with-param name="listsep2" select="$listsep2"/>
                    <xsl:with-param name="listsep3" select="$listsep3"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="normalize-space($list)!=''">
                    <!-- Top-level is single -->
                    <xsl:choose>
                        <xsl:when test="$list2!=''">
                            <!-- Analyse 2nd level -->
                            <xsl:choose>
                                <xsl:when test="contains($list2, $listsep)">
                                    <xsl:variable name="head2">
                                        <xsl:value-of select="substring-before($list2, $listsep)"/>
                                    </xsl:variable>
                                    <xsl:variable name="head3">
                                        <xsl:choose>
                                            <xsl:when test="contains($list3, $listsep3)">
                                                <xsl:value-of select="substring-before($list3, $listsep2)"/>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:value-of select="$list3"/>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:variable>
                                    <xsl:variable name="tail2">
                                        <xsl:value-of select="substring-after($list2, $listsep)"/>
                                    </xsl:variable>
                                    <xsl:variable name="tail3">
                                        <xsl:choose>
                                            <xsl:when test="contains($list3, $listsep3)">
                                                <xsl:value-of select="substring-after($list3, $listsep2)"/>
                                            </xsl:when>
                                            <!-- Otherwise Blank -->
                                        </xsl:choose>
                                    </xsl:variable>
                                    <xsl:call-template name="splitMultiList">
                                        <xsl:with-param name="arg" select="$arg"/>
                                        <xsl:with-param name="list" select="$list"/>
                                        <xsl:with-param name="list2" select="$head2"/>
                                        <xsl:with-param name="list3" select="$head3"/>
                                        <xsl:with-param name="listsep" select="$listsep"/>
                                        <xsl:with-param name="listsep2" select="$listsep2"/>
                                        <xsl:with-param name="listsep3" select="$listsep3"/>
                                    </xsl:call-template>
                                    <xsl:call-template name="splitMultiList">
                                        <xsl:with-param name="arg" select="$arg"/>
                                        <xsl:with-param name="list" select="$list"/>
                                        <xsl:with-param name="list2" select="$tail2"/>
                                        <xsl:with-param name="list3" select="$tail3"/>
                                        <xsl:with-param name="listsep" select="$listsep"/>
                                        <xsl:with-param name="listsep2" select="$listsep2"/>
                                        <xsl:with-param name="listsep3" select="$listsep3"/>
                                    </xsl:call-template>
                                </xsl:when>
                                <xsl:otherwise>
                                    <!-- 2nd-level is (now) single -->
                                    <xsl:choose>
                                        <xsl:when test="$list3!=''">
                                            <!-- Analyse 3rd level -->
                                            <xsl:choose>
                                                <xsl:when test="contains($list3, $listsep)">
                                                    <xsl:variable name="head3">
                                                        <xsl:value-of select="substring-before($list3, $listsep)"/>
                                                    </xsl:variable>
                                                    <xsl:variable name="tail3">
                                                        <xsl:value-of select="substring-after($list3, $listsep)"/>
                                                    </xsl:variable>
                                                    <xsl:call-template name="splitMultiList">
                                                        <xsl:with-param name="arg" select="$arg"/>
                                                        <xsl:with-param name="list" select="$list"/>
                                                        <xsl:with-param name="list2" select="$list2"/>
                                                        <xsl:with-param name="list3" select="$head3"/>
                                                        <xsl:with-param name="listsep" select="$listsep"/>
                                                        <xsl:with-param name="listsep2" select="$listsep2"/>
                                                        <xsl:with-param name="listsep3" select="$listsep3"/>
                                                    </xsl:call-template>
                                                    <xsl:call-template name="splitMultiList">
                                                        <xsl:with-param name="arg" select="$arg"/>
                                                        <xsl:with-param name="list" select="$list"/>
                                                        <xsl:with-param name="list2" select="$list2"/>
                                                        <xsl:with-param name="list3" select="$tail3"/>
                                                        <xsl:with-param name="listsep" select="$listsep"/>
                                                        <xsl:with-param name="listsep2" select="$listsep2"/>
                                                        <xsl:with-param name="listsep3" select="$listsep3"/>
                                                    </xsl:call-template>
                                                </xsl:when>
                                                <xsl:otherwise>
                                                    <!-- 3rd-level is (now) single -->
                                                    <xsl:call-template name="resource">
                                                        <xsl:with-param name="arg" select="$arg"/>
                                                        <xsl:with-param name="item" select="normalize-space($list)"/>
                                                        <xsl:with-param name="item2" select="normalize-space($list2)"/>
                                                        <xsl:with-param name="item3" select="normalize-space($list3)"/>
                                                    </xsl:call-template>
                                                </xsl:otherwise>
                                            </xsl:choose>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <!-- 1st/2nd levels only -->
                                            <xsl:call-template name="resource">
                                                <xsl:with-param name="arg" select="$arg"/>
                                                <xsl:with-param name="item" select="normalize-space($list)"/>
                                                <xsl:with-param name="item2" select="normalize-space($list2)"/>
                                            </xsl:call-template>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:otherwise>
                            <!-- Top-level only -->
                            <xsl:call-template name="resource">
                                <xsl:with-param name="arg" select="$arg"/>
                                <xsl:with-param name="item" select="normalize-space($list)"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>

    <!-- ****************************************************************** -->
    <!-- quoteSplit: split a set of strings that are seperated with a space
         and may or may not be enclosed within "".
         eg: This is "a string" . 
         output: ["This", "is", "a string"]

         @param string: the string containing the input
         @param inside_quotes: quotes on an inside string
    -->
    <xsl:template name="quoteSplit">
        <xsl:param name="string"/>
        
        <xsl:param name="inside_quotes" select="false"/>
        <xsl:variable name="normalized" select="normalize-space($string)"/>

        <xsl:choose>
            <xsl:when test="$normalized=''">
                <xsl:value-of select="''"/>
            </xsl:when>
            <xsl:when test="contains($normalized, '&quot;')">
                <xsl:variable name="head" select="substring-before($normalized, '&quot;')"/>
                <xsl:variable name="tail" select="substring-after($normalized, '&quot;')"/>
                <xsl:variable name="newhead">
                    <xsl:call-template name="quote">
                        <xsl:with-param name="string" select="$head"/>
                        <xsl:with-param name="inside_quotes" select="$inside_quotes"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="newtail">
                    <xsl:call-template name="quote">
                        <xsl:with-param name="string" select="$tail"/>
                        <xsl:with-param name="inside_quotes" select="not($inside_quotes)"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:choose>
                    <xsl:when test="$newhead!='' and $newtail!=''">
                        <xsl:value-of select="concat($newhead, ',', $newtail)"/>
                    </xsl:when>
                    <xsl:when test="$newhead!=''">
                        <xsl:value-of select="$newhead"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$newtail"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="contains($normalized, ' ') and not($inside_quotes)">
                <xsl:variable name="head" select="substring-before($normalized, ' ')"/>
                <xsl:variable name="tail" select="substring-after($normalized, ' ')"/>
                <xsl:variable name="newhead">
                    <xsl:call-template name="quote">
                        <xsl:with-param name="string" select="$head"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="newtail">
                    <xsl:call-template name="quote">
                        <xsl:with-param name="string" select="$tail"/>
                    </xsl:call-template>
                </xsl:variable>
                <xsl:choose>
                    <xsl:when test="$newhead!='' and $newtail!=''">
                        <xsl:value-of select="concat($newhead, ',', $newtail)"/>
                    </xsl:when>
                    <xsl:when test="$newhead!=''">
                        <xsl:value-of select="$newhead"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="$newtail"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="concat('&quot;', $normalized, '&quot;')"/>
            </xsl:otherwise>
        </xsl:choose>
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
        <xsl:variable name="labels" select="document('../s3csv/labels.xml')//labels"/>
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
        <xsl:variable name="lblmap" select="document('../s3csv/labels.xml')//labels/column[@name=$colname]"/>
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
