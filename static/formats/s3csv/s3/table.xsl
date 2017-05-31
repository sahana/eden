<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- **********************************************************************
        Dynamic Table Models - Import Stylesheet

        CSV fields:

        Table..............string..............the table name
        Field..............string..............the field name
        Label..............string..............the label for the field
        DataType...........string..............the data type of the field
        ComponentKey.......true|false..........use this field as component key
        ComponentAlias.....string..............the alias for the component
        ComponentTab.......true|false..........show the component on a tab
        Options............JSON................the field options
        Unique.............true|false..........field value must be unique
        Required...........true|false..........field value must not be empty
        DefaultValue.......string..............the default value for the field
        Settings...........JSON................field settings
        Comments...........string..............comment for the field to show in forms

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!-- ****************************************************************** -->

    <xsl:key name="tables" match="row" use="col[@field='Table']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">

        <s3xml>
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('tables', col[@field='Table'])[1])]">
                <xsl:call-template name="Table" />
            </xsl:for-each>
        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Table">

        <xsl:variable name="Name" select="col[@field='Table']/text()"/>

        <xsl:if test="$Name!=''">
            <resource name="s3_table">
                <data field="name">
                    <xsl:value-of select="$Name"/>
                </data>
                <xsl:for-each select="//row[col[@field='Table']/text()=$Name]">
                    <xsl:call-template name="Field"/>
                </xsl:for-each>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Field">

        <xsl:variable name="Name" select="col[@field='Field']/text()"/>
        <xsl:if test="$Name!=''">
            <resource name="s3_field">
                <data field="name">
                    <xsl:value-of select="$Name"/>
                </data>

                <xsl:variable name="DataType" select="col[@field='DataType']/text()"/>
                <data field="field_type">
                    <xsl:choose>
                        <xsl:when test="$DataType!=''">
                            <xsl:value-of select="$DataType"/>
                        </xsl:when>
                        <xsl:otherwise>string</xsl:otherwise>
                    </xsl:choose>
                </data>

                <xsl:variable name="ComponentKey" select="col[@field='ComponentKey']/text()"/>
                <data field="component_key">
                    <xsl:attribute name="value">
                        <xsl:choose>
                            <xsl:when test="$ComponentKey='true'">
                                <xsl:value-of select="'true'"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="'false'"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                </data>

                <xsl:variable name="ComponentAlias" select="col[@field='ComponentAlias']/text()"/>
                <xsl:if test="$ComponentAlias!=''">
                    <data field="component_alias">
                        <xsl:value-of select="$ComponentAlias"/>
                    </data>
                </xsl:if>

                <xsl:variable name="ComponentTab" select="col[@field='ComponentTab']/text()"/>
                <data field="component_tab">
                    <xsl:attribute name="value">
                        <xsl:choose>
                            <xsl:when test="$ComponentTab='true'">
                                <xsl:value-of select="'true'"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="'false'"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                </data>

                <xsl:variable name="Label" select="col[@field='Label']/text()"/>
                <xsl:if test="$Label!=''">
                    <data field="label">
                        <xsl:value-of select="$Label"/>
                    </data>
                </xsl:if>

                <xsl:variable name="Options" select="col[@field='Options']/text()"/>
                <xsl:if test="$Options!=''">
                    <data field="options">
                        <xsl:value-of select="$Options"/>
                    </data>
                </xsl:if>

                <xsl:variable name="DefaultValue" select="col[@field='DefaultValue']/text()"/>
                <xsl:if test="$DefaultValue!=''">
                    <data field="default_value">
                        <xsl:value-of select="$DefaultValue"/>
                    </data>
                </xsl:if>

                <xsl:variable name="Unique" select="col[@field='Unique']/text()"/>
                <data field="require_unique">
                    <xsl:attribute name="value">
                        <xsl:choose>
                            <xsl:when test="$Unique='true'">
                                <xsl:value-of select="'true'"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="'false'"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                </data>

                <xsl:variable name="Required" select="col[@field='Required']/text()"/>
                <data field="require_not_empty">
                    <xsl:attribute name="value">
                        <xsl:choose>
                            <xsl:when test="$Required='true'">
                                <xsl:value-of select="'true'"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="'false'"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                </data>

                <xsl:variable name="Settings" select="col[@field='Settings']/text()"/>
                <xsl:if test="$Settings!=''">
                    <data field="settings">
                        <xsl:value-of select="$Settings"/>
                    </data>
                </xsl:if>

                <xsl:variable name="Comments" select="col[@field='Comments']/text()"/>
                <xsl:if test="$Comments!=''">
                    <data field="comments">
                        <xsl:value-of select="$Comments"/>
                    </data>
                </xsl:if>

            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
