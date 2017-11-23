<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Questions - CSV Import Stylesheet

         CSV fields:
         Template....................dc_template.name
         Section.....................dc_question.section_id or dc_section.parent
         Section Position............dc_section.posn
         SubSection..................dc_question.section_id or dc_section.parent
         SubSection Position.........dc_section.posn (within parent section)
         SubSubSection...............dc_question.section_id
         SubSubSection Position......dc_section.posn (within parent section)
         Question....................dc_question.name
         Question Position...........dc_question.posn (within (Sub)Section)
         Type........................dc_question.field_type
         Options.....................dc_question.options
         #Sort........................dc_question.sort_options
         Required....................dc_question.require_not_empty
         Code........................dc_question.code
         Totals......................dc_question.totals
         Grid........................dc_question.grid
         Show Hidden.................dc_question.show_hidden
         Tooltip.....................dc_question.comments

    *********************************************************************** -->
    <xsl:output method="xml"/>
    <xsl:include href="../../xml/commons.xsl"/>

    <xsl:variable name="SectionPrefix" select="'Section:'"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="template" match="row" use="col[@field='Template']"/>

    <xsl:key name="section" match="row" use="concat(col[@field='Section'], '/',
                                                    col[@field='SubSection'], '/',
                                                    col[@field='SubSubSection'])"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>

            <!-- Templates -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('template',
                                                                       col[@field='Template'])[1])]">
                <xsl:call-template name="Template"/>
            </xsl:for-each>

            <!-- Sections -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('section',
                                                                   concat(col[@field='Section'], '/',
                                                                          col[@field='SubSection'], '/',
                                                                          col[@field='SubSubSection']))[1])]">
                <xsl:call-template name="Section">
                    <xsl:with-param name="Section">
                         <xsl:value-of select="col[@field='Section']"/>
                    </xsl:with-param>
                    <xsl:with-param name="SubSection">
                         <xsl:value-of select="col[@field='SubSection']"/>
                    </xsl:with-param>
                    <xsl:with-param name="SubSubSection">
                         <xsl:value-of select="col[@field='SubSubSection']"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:for-each>

            <!-- Questions -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">
        <xsl:variable name="Section">
            <xsl:value-of select="col[@field='Section']"/>
        </xsl:variable>

        <resource name="dc_question">
            <data field="name"><xsl:value-of select="col[@field='Question']"/></data>
            <data field="posn"><xsl:value-of select="col[@field='Question Position']"/></data>
            <data field="options"><xsl:value-of select="col[@field='Options']"/></data>
            <data field="code"><xsl:value-of select="col[@field='Code']"/></data>
            <data field="totals"><xsl:value-of select="col[@field='Totals']"/></data>
            <data field="grid"><xsl:value-of select="col[@field='Grid']"/></data>
            <data field="show_hidden"><xsl:value-of select="col[@field='Show Hidden']"/></data>
            <data field="comments"><xsl:value-of select="col[@field='Tooltip']"/></data>

            <!-- Sort Options
            <xsl:variable name="SortOptions">
                <xsl:call-template name="uppercase">
                    <xsl:with-param name="string">
                        <xsl:value-of select="col[@field='Sort']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="starts-with($SortOptions, 'Y') or starts-with($SortOptions, 'T')">
                    <data field="sort_options" value="true">True</data>
                </xsl:when>
                <xsl:when test="starts-with($SortOptions, 'N') or starts-with($SortOptions, 'F')">
                    <data field="sort_options" value="false">False</data>
                </xsl:when>
            </xsl:choose> -->

            <!-- Required -->
            <xsl:variable name="NotEmpty">
                <xsl:call-template name="uppercase">
                    <xsl:with-param name="string">
                        <xsl:value-of select="col[@field='Required']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="starts-with($NotEmpty, 'Y') or starts-with($NotEmpty, 'T')">
                    <data field="require_not_empty" value="true">True</data>
                </xsl:when>
                <xsl:when test="starts-with($NotEmpty, 'N') or starts-with($NotEmpty, 'F')">
                    <data field="require_not_empty" value="false">False</data>
                </xsl:when>
            </xsl:choose>

            <!-- Link to Template -->
            <reference field="template_id" resource="dc_template">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="col[@field='Template']"/>
                </xsl:attribute>
            </reference>

            <xsl:if test="$Section!=''">
                <!-- Link to Section -->
                <xsl:variable name="SubSection">
                    <xsl:value-of select="col[@field='SubSection']"/>
                </xsl:variable>
                <xsl:variable name="SubSubSection">
                    <xsl:value-of select="col[@field='SubSubSection']"/>
                </xsl:variable>
                <reference field="section_id" resource="dc_section">
                    <xsl:attribute name="tuid">
                        <xsl:choose>
                            <xsl:when test="$SubSubSection!=''">
                                <!-- Hierarchical Section with 3 levels -->
                                <xsl:value-of select="concat($SectionPrefix, $Section, '/', $SubSection, '/', $SubSubSection)"/>
                            </xsl:when>
                            <xsl:when test="$SubSection!=''">
                                <!-- Hierarchical Section with 2 levels -->
                                <xsl:value-of select="concat($SectionPrefix, $Section, '/', $SubSection)"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <!-- Simple Section -->
                                <xsl:value-of select="concat($SectionPrefix, $Section)"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                </reference>
            </xsl:if>

            <!-- Field Type -->
            <xsl:variable name="Type">
                <xsl:call-template name="uppercase">
                    <xsl:with-param name="string">
                        <xsl:value-of select="col[@field='Type']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="$Type='TEXT' or $Type='STRING'">
                    <data field="field_type">1</data>
                </xsl:when>
                <xsl:when test="$Type='NUMBER' or $Type='INTEGER'">
                    <data field="field_type">2</data>
                </xsl:when>
                <xsl:when test="$Type='FRACTION' or $Type='FLOAT'">
                    <data field="field_type">3</data>
                </xsl:when>
                <xsl:when test="$Type='YES/NO' or $Type='Y/N' or $Type='BOOLEAN'">
                    <data field="field_type">4</data>
                </xsl:when>
                <xsl:when test="$Type='YES/NO/DONT KNOW' or $Type='Y/N/DK'">
                    <data field="field_type">5</data>
                </xsl:when>
                <xsl:when test="$Type='OPTIONS' or $Type='SELECT'">
                    <data field="field_type">6</data>
                </xsl:when>
                <xsl:when test="$Type='DATE'">
                    <data field="field_type">7</data>
                </xsl:when>
                <xsl:when test="$Type='DATETIME'">
                    <data field="field_type">8</data>
                </xsl:when>
                <xsl:when test="$Type='GRID' or $Type='TABLE'">
                    <data field="field_type">9</data>
                </xsl:when>
                <xsl:when test="$Type='COMMENTS' or $Type='PARAGRAPH'">
                    <data field="field_type">10</data>
                </xsl:when>
                <xsl:when test="$Type='RICHTEXT'">
                    <data field="field_type">11</data>
                </xsl:when>
                <xsl:otherwise>
                    <!-- Default to String -->
                    <data field="field_type">1</data>
                </xsl:otherwise>
            </xsl:choose>

            <!-- Required -->
            <xsl:variable name="Required">
                <xsl:call-template name="uppercase">
                    <xsl:with-param name="string">
                        <xsl:value-of select="col[@field='Required']/text()"/>
                    </xsl:with-param>
                </xsl:call-template>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="starts-with($Required, 'Y') or starts-with($Required, 'T')">
                    <data field="require_not_empty" value="true">True</data>
                </xsl:when>
                <xsl:when test="starts-with($Required, 'N') or starts-with($Required, 'F')">
                    <data field="require_not_empty" value="false">False</data>
                </xsl:when>
            </xsl:choose>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Template">
        <xsl:variable name="template" select="col[@field='Template']/text()"/>

        <resource name="dc_template">
            <xsl:attribute name="tuid">
                <xsl:value-of select="$template"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$template"/></data>
       </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Section">
        <!-- @todo: migrate to Taxonomy-pattern, see vulnerability/data.xsl -->
        <xsl:param name="Section"/>
        <xsl:param name="SubSection"/>
        <xsl:param name="SubSubSection"/>

        <xsl:if test="$Section!=''">
            <resource name="dc_section">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($SectionPrefix, $Section)"/>
                </xsl:attribute>
                <data field="name"><xsl:value-of select="$Section"/></data>
                <data field="posn"><xsl:value-of select="col[@field='Section Position']"/></data>
                <!-- Link to Template -->
                <reference field="template_id" resource="dc_template">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="col[@field='Template']"/>
                    </xsl:attribute>
                </reference>
            </resource>
            <xsl:if test="$SubSection!=''">
                <resource name="dc_section">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($SectionPrefix, $Section, '/', $SubSection)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$SubSection"/></data>
                    <data field="posn"><xsl:value-of select="col[@field='SubSection Position']"/></data>
                    <!-- Link to Template -->
                    <reference field="template_id" resource="dc_template">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='Template']"/>
                        </xsl:attribute>
                    </reference>
                    <reference field="parent" resource="dc_section">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($SectionPrefix, $Section)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
            <xsl:if test="$SubSubSection!=''">
                <resource name="dc_section">
                    <xsl:attribute name="tuid">
                        <xsl:value-of select="concat($SectionPrefix, $Section, '/', $SubSection, '/', $SubSubSection)"/>
                    </xsl:attribute>
                    <data field="name"><xsl:value-of select="$SubSubSection"/></data>
                    <data field="posn"><xsl:value-of select="col[@field='SubSubSection Position']"/></data>
                    <!-- Link to Template -->
                    <reference field="template_id" resource="dc_template">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="col[@field='Template']"/>
                        </xsl:attribute>
                    </reference>
                    <reference field="parent" resource="dc_section">
                        <xsl:attribute name="tuid">
                            <xsl:value-of select="concat($SectionPrefix, $Section, '/', $SubSection)"/>
                        </xsl:attribute>
                    </reference>
                </resource>
            </xsl:if>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
